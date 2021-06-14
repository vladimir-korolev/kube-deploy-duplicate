{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "ddprofiler-rc.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ddprofiler-rc.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ddprofiler-rc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "ddprofiler-rc.labels" -}}
helm.sh/chart: {{ include "ddprofiler-rc.chart" . }}
{{ include "ddprofiler-rc.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "ddprofiler-rc.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ddprofiler-rc.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "ddprofiler-rc.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "ddprofiler-rc.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}



{{/*
Creates all roles
*/}}
{{- define "roles" }}
{{- range $key, $value := .namespace }}
---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: {{ $key }}
  name: {{ $.role }}
rules:
    {{- range $key, $value := .rules }}
- apiGroups: {{ $value.apiGroups }}
  resources: {{ $value.resources }}
  verbs: {{ $value.verbs }}
    {{- end }}
  {{- end }}
{{- end -}}

{{/*
Creates all role bindings
*/}}
{{- define "role.binding" }}
{{- range $key, $value := .namespace }}
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: {{ $.role }}-binding
  namespace: {{ $key }}
subjects:
- kind: ServiceAccount
  name: {{ $.role }}
  namespace: {{ $key }}
roleRef:
  kind: Role
  name: {{ $.role }}
  apiGroup: rbac.authorization.k8s.io
  {{- end }}
{{- end -}}


{{/*
Creates all role permissions
*/}}
{{- define "roles_permissions" }}
    {{- range $key, $value := .roles_permissions }}
- apiGroups: {{ $value.apiGroups }}
  resources: {{ $value.resources }}
  verbs: {{ $value.verbs }}
    {{- end }}
{{- end -}}