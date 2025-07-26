{{/*
Expand the name of the chart.
*/}}
{{- define "execution-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "execution-api.fullname" -}}
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
{{- define "execution-api.labels" -}}
helm.sh/chart: {{ include "execution-api.name" . }}
{{ include "execution-api.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels that will be used to identify all pods.
*/}}
{{- define "execution-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "execution-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
