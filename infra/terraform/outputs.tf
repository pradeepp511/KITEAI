output "project_id" {
  value = google_project.project.project_id
}

output "timescaledb_instance_name" {
  value = google_sql_database_instance.timescaledb.name
}

output "timescaledb_instance_connection_name" {
  value = google_sql_database_instance.timescaledb.connection_name
}
