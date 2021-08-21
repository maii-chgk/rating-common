/* WIP и черновик, ещё не протестированный витриной */

create table b.release_details (
    id int primary key,
    date timestamp,
    updated_at timestamp,
    title text
);

create table b.releases
(
	id int
		constraint releases_pk
			primary key,
	team_id int,
	release_details_id int
		constraint table_name_release_details_id_fk
			references b.release_details,
	rating int,
	rating_change int
);

create index table_name_id_team_id_index
	on b.releases (id desc, team_id asc);
  
