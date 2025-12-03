{{/*
Expand the name of the chart.
*/}}
{{- define "911-training.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "911-training.fullname" -}}
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
Create chart name and version as used by the chart label.
*/}}
{{- define "911-training.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "911-training.labels" -}}
helm.sh/chart: {{ include "911-training.chart" . }}
{{ include "911-training.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "911-training.selectorLabels" -}}
app.kubernetes.io/name: {{ include "911-training.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "911-training.frontend.labels" -}}
{{ include "911-training.labels" . }}
app: 911-training-simulator
component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "911-training.frontend.selectorLabels" -}}
{{ include "911-training.selectorLabels" . }}
app: 911-training-simulator
component: frontend
{{- end }}

{{/*
Backend labels
*/}}
{{- define "911-training.backend.labels" -}}
{{ include "911-training.labels" . }}
app: 911-training-simulator
component: backend
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "911-training.backend.selectorLabels" -}}
{{ include "911-training.selectorLabels" . }}
app: 911-training-simulator
component: backend
{{- end }}

{{/*
Coqui TTS labels
*/}}
{{- define "911-training.coquiTts.labels" -}}
{{ include "911-training.labels" . }}
app: 911-training-simulator
component: coqui-tts
{{- end }}

{{/*
Coqui TTS selector labels
*/}}
{{- define "911-training.coquiTts.selectorLabels" -}}
{{ include "911-training.selectorLabels" . }}
app: 911-training-simulator
component: coqui-tts
{{- end }}

{{/*
PostgreSQL labels
*/}}
{{- define "911-training.postgresql.labels" -}}
{{ include "911-training.labels" . }}
app: 911-training-simulator
component: database
{{- end }}

{{/*
PostgreSQL selector labels
*/}}
{{- define "911-training.postgresql.selectorLabels" -}}
{{ include "911-training.selectorLabels" . }}
app: 911-training-simulator
component: database
{{- end }}

{{/*
Redis labels
*/}}
{{- define "911-training.redis.labels" -}}
{{ include "911-training.labels" . }}
app: 911-training-simulator
component: redis
{{- end }}

{{/*
Redis selector labels
*/}}
{{- define "911-training.redis.selectorLabels" -}}
{{ include "911-training.selectorLabels" . }}
app: 911-training-simulator
component: redis
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "911-training.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "911-training.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "911-training.databaseUrl" -}}
postgresql://{{ .Values.postgresql.config.username }}:{{ .Values.postgresql.secrets.password }}@postgresql-service:{{ .Values.postgresql.service.port }}/{{ .Values.postgresql.config.database }}
{{- end }}
