create materialized view teams as
  select rating_team.r_id as id, rating_team.title as name, rt.title as city
  from rating_team
  left join rating_town rt on rating_team.town_id = rt.id;

create materialized view tournaments as
    select tour.r_id as id, tour.title as name,
           tour.start_datetime as start_date,
           tour.end_datetime as end_date,
           tour_type.title as type
    from rating_tournament tour
    left join rating_typeoft tour_type on tour.typeoft_id = tour_type.id;
    
create materialized view tournament_results as
    select tourn.r_id as tournament_id,
           team.r_id as team_id,
           team_title as team_name,
           total as points,
           position as place
    from rating_result res
    left join rating_tournament tourn on res.tournament_id = tourn.id
    left join rating_team team on res.team_id = team.id;
    
create materialized view tournament_players as
    select player.r_id as player_id,
           tourn.r_id as tournament_id,
           team.r_id as team_id,
           ro.flag
    from "rating_result_teamMembers"
    left join rating_player player on "rating_result_teamMembers".player_id = player.id
    left join rating_result res on "rating_result_teamMembers".result_id = res.id
    left join rating_tournament tourn on res.tournament_id = tourn.id
    left join rating_team team on res.team_id = team.id
    left join rating_oldrating ro on res.id = ro.result_id and player.id = ro.player_id;
