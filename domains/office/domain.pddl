(define (domain officeworld)

  (:requirements
    :strips :adl
  )

  (:predicates
    (visited-A)
    (visited-B)
    (visited-C)
    (visited-D)
    (visited-mail)
    (visited-coffee)
    (delivered-coffee)
    (delivered-mail)
  )

  (:action goto-a
    :parameters ()
    :precondition ()
    :effect (and
              (visited-A)
              )
    )

  (:action goto-b
    :parameters ()
    :precondition ()
    :effect (and
              (visited-B)
              )
    )

  (:action goto-c
    :parameters ()
    :precondition ()
    :effect (and
              (visited-C)
              )
    )

  (:action goto-d
    :parameters ()
    :precondition ()
    :effect (and
              (visited-D)
              )
    )

  (:action goto-mail
    :parameters ()
    :precondition ()
    :effect (and
              (visited-mail)
              )
    )

  (:action goto-coffee
    :parameters ()
    :precondition ()
    :effect (and
              (visited-coffee)
              )
    )

  (:action goto-office
    :parameters ()
    :precondition ()
    :effect (and
              (when (visited-mail) (delivered-mail))
              (when (visited-coffee) (delivered-coffee))
              )
    )
)
