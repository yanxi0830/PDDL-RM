(define (problem t0)
	(:domain boxworld)
	(:objects
    key-a key-b key-c gem
	)
	(:init
    (loose key-a)
    (locks key-a key-b)
    (locks key-a key-c)
    (locks key-b gem)
    (empty-hand)
	)
	(:goal (and
    (holding gem)
		)
	)
)
