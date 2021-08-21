SELECT 
        t.title
      , main.team_title
      , main.position
      , main.total
      , pl.last_name
      , pl.first_name
      , pl.patronymic
      , t.r_id tournament_id
      , main.team_id
      , pl.r_id player
      , main.flags
      , t.start_datetime
      , t.end_datetime
      , tof.title
      , t."questionQty"
      --, main.mask
FROM rating_result main
left outer join rating_tournament t on
    main.tournament_id=t.id
left outer join "rating_result_teamMembers" r on
    main.id=r.result_id
left outer join rating_player pl on
    r.player_id=pl.id
left outer join rating_typeoft tof on
    tof.id=t.typeoft_id
