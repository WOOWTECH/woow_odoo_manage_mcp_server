{{/*
Helpers for the odoo-manage-mcp chart.

Object names are FIXED (mcp-odoo-ivnvxd-admin*), not derived from the release
name: they are what the legacy manifest created, what the Cloudflare Tunnel
route points at, and what the Deployment selector matches. Deriving them from
.Release.Name would rename the Service (breaking the tunnel route) and change
the immutable selector. One release per namespace keeps them unique.
*/}}

{{- define "odooManageMcp.name" -}}
mcp-odoo-ivnvxd-admin
{{- end -}}

{{- define "odooManageMcp.ns" -}}
{{ default .Release.Namespace .Values.namespace.name }}
{{- end -}}

{{- define "odooManageMcp.partOf" -}}
{{ required "instance.partOf is required: the customer/instance slug used as app.kubernetes.io/part-of" .Values.instance.partOf }}
{{- end -}}

{{- define "odooManageMcp.odooUrl" -}}
{{ required "odoo.url is required: the in-cluster Odoo URL, e.g. http://lyucijyun-odoo-svc:8069" .Values.odoo.url }}
{{- end -}}

{{/* Labels on every object. */}}
{{- define "odooManageMcp.labels" -}}
app.kubernetes.io/component: {{ include "odooManageMcp.name" . }}
app.kubernetes.io/part-of: {{ include "odooManageMcp.partOf" . }}
{{- end -}}

{{/* Selector / pod-template labels. Immutable on the Deployment - never change. */}}
{{- define "odooManageMcp.selectorLabels" -}}
app.kubernetes.io/component: {{ include "odooManageMcp.name" . }}
app.kubernetes.io/name: {{ include "odooManageMcp.name" . }}
{{- end -}}

{{/* `annotations:` block with the keep policy, or nothing. */}}
{{- define "odooManageMcp.keepAnnotations" -}}
{{- if .Values.keepOnUninstall -}}
annotations:
  helm.sh/resource-policy: keep
{{- end -}}
{{- end -}}

{{/* Container image: the prebuilt admin image, or the base python image when
     the sources are built at pod start. */}}
{{- define "odooManageMcp.image" -}}
{{- if .Values.buildFromSource.enabled -}}
{{ .Values.buildFromSource.images.python }}
{{- else -}}
{{ .Values.image.repository }}:{{ .Values.image.tag }}
{{- end -}}
{{- end -}}
