with main as
(
    SELECT
            row_number() over (order by t.start_datetime, pl.id) id
          , t.title tournament
          , main.team_title team
          , main.position
          , main.total
          , pl.last_name
          , pl.first_name
          , pl.patronymic
          , case 
              when ind.flag is null then 'Л'
              else ind.flag
            end flag
          , t.id tournament_id
          , team.id team_id
          , pl.id player_id
          , t.start_datetime
          , t.end_datetime
          , tof.title kind
          , t."questionQty" tournament_distance
          , rtg."inRating" is_rating
          , rtg."predictedPosition" predicted_position
          , rtg.rg predicted_bonus
          , rtg.d rating_result
          , r.result_id team_in_tournament
          , ind.rating individual_rating
          , ind."usedRating" individual_rating_in_tournament
    FROM rating_result main
    left outer join rating_tournament t on
        main.tournament_id=t.id
    left outer join "rating_result_teamMembers" r on
        main.id=r.result_id
    left outer join rating_player pl on
        r.player_id=pl.id
    left outer join rating_team team on
        team.id=main.team_id
    left outer join rating_oldteamrating rtg on
        r.result_id=rtg.result_id
    left outer join rating_typeoft tof on
        tof.id=t.typeoft_id
    left outer join rating_oldrating ind on
        ind.result_id=r.result_id and
        ind.player_id=pl.id
    where 
    t.start_datetime>='2018-01-01' and
    t.end_datetime<='2020-03-01' and
    rtg."inRating"=True
)

