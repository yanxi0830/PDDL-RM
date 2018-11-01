from krrt.utils import get_opts, write_file
from krrt.planning.strips.representation import parse_problem, generate_action, Action
from krrt.planning import parse_output_FF, parse_output_popf, parse_output_ipc, parse_output_mp
from krrt.sat.CNF import OptimizedLevelWeightedFormula

from linearizer import count_linearizations
from lifter import lift_POP, make_layered_POP

import networkx as nx

USAGE_STRING = "\n\
Usage: python encoder.py -<option> <argument> -<option> <argument> ... <FLAG> <FLAG> ...\n\n\
\n\
        Where options are:\n\
          -domain <pddl domain file>\n\
          -prob <pddl problem file>\n\
          -ffout <captured FF output>\n\
          -popfout <captured POPF output>\n\
          -mercout <captured Mercury output>\n\
          -mpout <captured Mp output>\n\
          -output <output file basename>\n\
\n\
        And the flags include:\n\
          SERIAL: Force it to be serial.\n\
          ALLACT: Include all actions.\n\
          DEORDER: Only allow deorderings.\n\
        "


def encode_POP(dom, prob, pop, output, flags):
    # For sanitization, make sure we close the pop
    pop.transativly_close()

    allF, allA, I, G = parse_problem(dom, prob)

    F = pop.F
    A = pop.A
    I = pop.I
    G = pop.G

    init = pop.init
    goal = pop.goal

    adders = {}
    deleters = {}

    for f in F:
        adders[f] = set([])
        deleters[f] = set([])

    for a in A:
        for f in a.adds:
            adders[f].add(a)
        for f in a.dels:
            deleters[f].add(a)

    VARNUM = 1

    # Create the vars for each action
    v2a = {}
    a2v = {}
    for a in A:
        v2a[VARNUM] = a
        a2v[a] = VARNUM
        VARNUM += 1

    # Create the vars for each action ordering
    v2o = {}
    o2v = {}
    for a1 in A:
        for a2 in A:
            v2o[VARNUM] = (a1, a2)
            o2v[(a1, a2)] = VARNUM
            VARNUM += 1

    # Create the vars for each possible action support
    v2s = {}
    s2v = {}
    for a2 in A:
        for p in a2.precond:
            for a1 in adders[p]:
                v2s[VARNUM] = (a1, p, a2)
                s2v[(a1, p, a2)] = VARNUM
                VARNUM += 1

    formula = OptimizedLevelWeightedFormula()

    # Add the antisymmetric ordering constraints
    for a in A:
        formula.addClause([-o2v[(a, a)]])

    # Add the transitivity constraints
    for a1 in A:
        for a2 in A:
            for a3 in A:
                formula.addClause([-o2v[(a1, a2)], -o2v[(a2, a3)], o2v[(a1, a3)]])

    # Add the ordering -> actions constraints
    for a1 in A:
        for a2 in A:
            formula.addClause([-o2v[(a1, a2)], a2v[a1]])
            formula.addClause([-o2v[(a1, a2)], a2v[a2]])

    # Make sure everything comes after the init, and before the goal
    for a in A:
        if a is not init:
            formula.addClause([-a2v[a], o2v[(init, a)]])
        if a is not goal:
            formula.addClause([-a2v[a], o2v[(a, goal)]])

    # Ensure that we have a goal and init action.
    formula.addClause([a2v[init]])
    formula.addClause([a2v[goal]])

    # Satisfy all the preconditions
    for a2 in A:
        for p in a2.precond:
            formula.addClause([-a2v[a2]] + [s2v[(a1, p, a2)] for a1 in filter(lambda x: x is not a2, adders[p])])

    # Create unthreatened support
    for a2 in A:
        for p in a2.precond:
            for a1 in filter(lambda x: x is not a2, adders[p]):

                # Support implies ordering
                formula.addClause([-s2v[(a1, p, a2)], o2v[(a1, a2)]])

                # Forbid threats
                # print "%s--%s-->%s: %s" % (str(a1), str(p), str(a2), str(deleters[p]))
                for ad in filter(lambda x: x not in set([a1, a2]), deleters[p]):
                    # print "...%s--%s-->%s: %s" % (str(a1), str(p), str(a2), str(ad))
                    formula.addClause([-s2v[(a1, p, a2)], -a2v[ad], o2v[(ad, a1)], o2v[(a2, ad)]])

    # Add the main constraints that satisfy preconditions without threats
    # for a in A:
    # total = []

    # for p in a.precond:
    # subtheories = []
    # for achiever in adders[p]:
    # if achiever is not a:
    # subtheory = [set([o2v[(achiever, a)]])]
    # for deleter in deleters[p]:
    # if deleter is not a:
    # subtheory.append(set([-a2v[deleter], o2v[(deleter, achiever)], o2v[(a, deleter)]]))
    # subtheories.append(subtheory)

    # mastertheory = subtheories.pop()

    # while subtheories:
    # currenttheory = subtheories.pop()
    # mastertheory = [i | j for i in mastertheory for j in currenttheory]

    # total.extend(mastertheory)

    # total = [item | set([-a2v[a]]) for item in total]

    # for cls in total:
    # assert cls.__class__ == set
    # hard_clauses.append(cls)

    if 'SERIAL' in flags:
        for a1 in A:
            for a2 in A:
                if a1 is not a2:
                    formula.addClause([-a2v[a1], -a2v[a2], o2v[(a1, a2)], o2v[(a2, a1)]])

    if 'ALLACT' in flags:
        for a in A:
            formula.addClause([a2v[a]])

    if 'DEORDER' in flags:
        for (ai, aj) in pop.get_links():
            formula.addClause([-o2v[(aj, ai)]])

    # Now add the soft clauses.
    for a1 in A:
        for a2 in A:
            formula.addClause([-o2v[(a1, a2)]], 1, 1)

        # formula.addClause([Not(a1)], COST, 2)
        formula.addClause([-a2v[a1]], 1, 2)

    formula.writeCNF(output + '.wcnf')
    formula.writeCNF(output + '.cnf', hard=True)
    mapping_lines = []
    for v in v2a:
        mapping_lines.append("%d %s in plan" % (v, str(v2a[v])))
    for v in v2o:
        mapping_lines.append("%d %s is ordered before %s" % (v, str(v2o[v][0]), str(v2o[v][1])))
    for v in v2s:
        mapping_lines.append("%d %s supports %s with %s" % (v, str(v2s[v][0]), str(v2s[v][2]), str(v2s[v][1])))
    write_file(output + '.map', mapping_lines)

    print ''
    print "Vars: %d" % formula.num_vars
    print "Clauses: %d" % formula.num_clauses
    print "Soft: %d" % len(formula.getSoftClauses())
    print "Hard: %d" % len(formula.getHardClauses())
    print "Max Weight: %d" % formula.top_weight
    print ''


def encode_manual_domain():
    domain = "../domains/craft/domain.pddl"
    prob = "../domains/craft/t10.pddl"
    plan = parse_output_ipc("../domains/craft/t10.plan")

    pop = lift_POP(domain, prob, plan, True)
    print pop.network.nodes

    popfile = "../results/pop"
    encode_POP(domain, prob, pop, popfile, {})


if __name__ == '__main__':
    encode_manual_domain()
#
# if __name__ == '__main__':
#     import os
#
#     myargs, flags = get_opts()
#
#     if not myargs.has_key('-domain'):
#         print "Must include domain to lift:"
#         print USAGE_STRING
#         os._exit(1)
#
#     dom = myargs['-domain']
#
#     if not myargs.has_key('-prob'):
#         print "Must include problem to lift:"
#         print USAGE_STRING
#         os._exit(1)
#
#     prob = myargs['-prob']
#
#     if '-ffout' in myargs:
#         plan = parse_output_FF(myargs['-ffout'])
#         pop = lift_POP(dom, prob, plan, True)
#     elif '-mercout' in myargs:
#         plan = parse_output_ipc(myargs['-mercout'])
#         pop = lift_POP(dom, prob, plan, True)
#     elif '-popfout' in myargs:
#         popfout = myargs['-popfout']
#         layered_plan = parse_output_popf(popfout)
#         pop = make_layered_POP(layered_plan, dom, prob, popfout)
#     elif '-mpout' in myargs:
#         mpout = myargs['-mpout']
#         layered_plan = parse_output_mp(mpout)
#         pop = make_layered_POP(layered_plan, dom, prob, mpout)
#     else:
#         assert False, "Error: No recognized planner specified."
#
#     if not myargs.has_key('-output'):
#         print "Must include output CNF file:"
#         print USAGE_STRING
#         os._exit(1)
#
#     output = myargs['-output']
#
#     encode_POP(dom, prob, pop, output, flags)
