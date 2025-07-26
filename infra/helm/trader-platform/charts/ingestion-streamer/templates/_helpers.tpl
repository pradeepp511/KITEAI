{{/*
Expand the name of the chart.
*/}}
{{- define "ingestion-streamer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ingestion-streamer.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart-level labels to be applied to every resource.
*/}}
{{- define "ingestion-streamer.labels" -}}
helm.sh/chart: {{ include "ingestion-streamer.name" . }}
{{ include "ingestion-streamer.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels that will be used to identify all pods.
*/}}
{{- define "ingestion-streamer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ingestion-streamer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
