drop table if exists jobs;
create table jobs (
  internal_job_id integer primary key autoincrement,
  pdb2pqr_job_id integer not null,
  email varchar(1024),
  pdb_id varchar(10),
  pdb_file varchar(64000),
  job_info varchar(32000)
);