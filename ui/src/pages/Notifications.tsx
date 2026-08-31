import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Mail, Plus, Send, Trash2, Webhook } from "lucide-react";
import { notificationChannelsApi } from "@/services/api";
import type { NotificationChannel } from "@/types";
import { useLanguage } from "@/i18n/LanguageContext";

const DEFAULT_WEBHOOK_TEMPLATE = JSON.stringify(
  {
    msgtype: "text",
    text: {
      content:
        "[{{severity}}] {{type}}\nRepository: {{repository}}\nFile: {{file}}\n{{description}}",
    },
  },
  null,
  2,
);

export const Notifications: React.FC = () => {
  const { t } = useLanguage();
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["notification-channels"],
    queryFn: notificationChannelsApi.list,
    refetchInterval: 5000,
    refetchIntervalInBackground: false,
    staleTime: 0,
  });
  const [showForm, setShowForm] = useState(false);
  const [testResult, setTestResult] = useState<{
    channelId: number;
    success: boolean;
  } | null>(null);
  const [form, setForm] = useState({
    name: "",
    channel_type: "email" as "email" | "webhook",
    target: "",
    body_template: "",
    enabled: true,
  });
  const add = useMutation({
    mutationFn: notificationChannelsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notification-channels"] });
      setForm({
        name: "",
        channel_type: "email",
        target: "",
        body_template: "",
        enabled: true,
      });
      setShowForm(false);
    },
  });
  const update = useMutation({
    mutationFn: ({
      channel,
      enabled,
    }: {
      channel: NotificationChannel;
      enabled: boolean;
    }) => notificationChannelsApi.update(channel.id, { enabled }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["notification-channels"] }),
  });
  const remove = useMutation({
    mutationFn: notificationChannelsApi.delete,
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["notification-channels"] }),
  });
  const testChannel = useMutation({
    mutationFn: notificationChannelsApi.test,
    onMutate: () => setTestResult(null),
    onSuccess: (_, channelId) => setTestResult({ channelId, success: true }),
    onError: (_, channelId) => setTestResult({ channelId, success: false }),
  });
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Bell className="h-4 w-4" />
          <span>
            {t(
              "Notifications are sent after a scan finishes whenever it has findings.",
            )}
          </span>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          <Plus className="h-4 w-4" />
          {showForm ? t("Collapse") : t("Add Notification Channel")}
        </button>
      </div>
      {showForm && (
        <form
          className="rounded-xl border bg-card p-5 shadow-sm"
          onSubmit={(e) => {
            e.preventDefault();
            add.mutate(form);
          }}
        >
          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            {(["email", "webhook"] as const).map((type) => {
              const Icon = type === "email" ? Mail : Webhook;
              return (
                <button
                  type="button"
                  key={type}
                  onClick={() =>
                    setForm({
                      ...form,
                      channel_type: type,
                      target: "",
                      body_template:
                        type === "webhook" ? DEFAULT_WEBHOOK_TEMPLATE : "",
                    })
                  }
                  className={`flex items-center gap-3 rounded-lg border p-3 text-left ${form.channel_type === type ? "border-primary bg-primary/5" : ""}`}
                >
                  <span className="rounded-lg bg-muted p-2 text-primary">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span>
                    <strong className="block text-sm">
                      {t(type === "email" ? "Email" : "Webhook")}
                    </strong>
                    <small className="text-muted-foreground">
                      {t(
                        type === "email"
                          ? "Send to the security team mailbox"
                          : "Push to an HTTPS endpoint",
                      )}
                    </small>
                  </span>
                </button>
              );
            })}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="mb-1.5 block font-medium">
                {t("Channel Name")}
              </span>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </label>
            <label className="text-sm">
              <span className="mb-1.5 block font-medium">
                {t(
                  form.channel_type === "email"
                    ? "Email Address"
                    : "Webhook URL",
                )}
              </span>
              <input
                required
                type={form.channel_type === "email" ? "email" : "url"}
                value={form.target}
                onChange={(e) => setForm({ ...form, target: e.target.value })}
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </label>
          </div>
          {form.channel_type === "webhook" && (
            <label className="mt-4 block text-sm">
              <span className="mb-1.5 block font-medium">
                {t("Webhook Template")}
              </span>
              <textarea
                rows={10}
                value={form.body_template}
                onChange={(e) =>
                  setForm({ ...form, body_template: e.target.value })
                }
                className="w-full rounded-md border bg-background px-3 py-2 font-mono text-xs"
              />
              <span className="mt-1 block text-xs text-muted-foreground">
                {t(
                  "Valid JSON. Use placeholders: {{severity}}, {{type}}, {{repository}}, {{file}}, {{line}}, {{description}}, {{commit_hash}}, {{commit_url}}, {{value_preview}}, {{last_seen_at}}.",
                )}
              </span>
            </label>
          )}
          {add.isError && (
            <p className="mt-3 text-sm text-destructive">
              {t(
                "Failed to create channel. Check the input and service configuration.",
              )}
            </p>
          )}
          <div className="mt-4 flex justify-end">
            <button
              disabled={add.isPending}
              className="rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground"
            >
              {add.isPending ? t("Saving...") : t("Save Channel")}
            </button>
          </div>
        </form>
      )}
      {isLoading ? (
        <div className="rounded-xl border p-8 text-center text-muted-foreground">
          {t("Loading...")}
        </div>
      ) : data.length === 0 ? (
        <div className="rounded-xl border border-dashed p-10 text-center">
          <Bell className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-3 font-medium">{t("No notification channels")}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("Create an Email or Webhook channel to receive risk alerts.")}
          </p>
        </div>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {data.map((channel) => {
            const Icon = channel.channel_type === "email" ? Mail : Webhook;
            return (
              <article
                key={channel.id}
                className="rounded-xl border bg-card p-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex min-w-0 gap-3">
                    <span
                      className={`rounded-lg p-2 ${channel.enabled ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}
                    >
                      <Icon className="h-5 w-5" />
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h2 className="truncate font-semibold">
                          {channel.name}
                        </h2>
                        <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium">
                          {channel.enabled ? t("Enabled") : t("Disabled")}
                        </span>
                      </div>
                      <p
                        className="mt-1 truncate text-xs text-muted-foreground"
                        title={channel.target}
                      >
                        {channel.target}
                      </p>
                      {channel.channel_type === "webhook" && (
                        <p className="mt-1 text-xs text-primary">
                          {channel.body_template
                            ? t("Custom template")
                            : t("Default JSON payload")}
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    title={t("Delete Channel")}
                    disabled={remove.isPending}
                    onClick={() => {
                      if (
                        window.confirm(
                          `${t("Delete Channel")} "${channel.name}"?`,
                        )
                      )
                        remove.mutate(channel.id);
                    }}
                    className="rounded-md p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t pt-3">
                  <div>
                    <span className="text-xs uppercase text-muted-foreground">
                      {channel.channel_type}
                    </span>
                    {testResult?.channelId === channel.id && (
                      <span
                        className={`ml-3 text-xs ${testResult.success ? "text-emerald-600" : "text-destructive"}`}
                      >
                        {t(
                          testResult.success
                            ? "Test notification sent."
                            : "Test notification failed.",
                        )}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      disabled={testChannel.isPending}
                      onClick={() => testChannel.mutate(channel.id)}
                      className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                    >
                      <Send className="h-3.5 w-3.5" />
                      {testChannel.isPending &&
                      testChannel.variables === channel.id
                        ? t("Sending...")
                        : t("Send Test")}
                    </button>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={channel.enabled}
                      disabled={update.isPending}
                      onClick={() =>
                        update.mutate({ channel, enabled: !channel.enabled })
                      }
                      className={`relative h-6 w-11 rounded-full ${channel.enabled ? "bg-emerald-500" : "bg-muted"}`}
                    >
                      <span
                        className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${channel.enabled ? "translate-x-5" : ""}`}
                      />
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
};
