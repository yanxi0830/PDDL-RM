(define (domain boxworld)

  (:requirements
    :strips :adl
  )

  (:predicates
    (holding ?obj)  ; holding key or gem
    (empty-hand)
    (locks ?key ?obj)
    (loose ?key)
  )

  (:action get-obj
    :parameters (?key-have ?obj-get)
    :precondition (and
                    (holding ?key-have)
                    (locks ?key-have ?obj-get))
    :effect (and
              (not (holding ?key-have))
              (not (locks ?key-have ?obj-get))
              (holding ?obj-get)
              )
    )

  (:action get-loose-key
    :parameters (?key)
    :precondition (and
                    (empty-hand)
                    (loose ?key))
    :effect (and
              (not (empty-hand))
              (holding ?key))
    )
)
