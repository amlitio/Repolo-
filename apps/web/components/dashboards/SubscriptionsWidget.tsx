"use client";

import { useState } from "react";
import {
  useCreateSubscription,
  useSendTestNotification,
  useSubscriptions,
} from "@/lib/hooks/useSubscriptions";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";

export function SubscriptionsWidget({ defaultCountyFips }: { defaultCountyFips?: string }) {
  const { data, isLoading, isError, error, refetch } = useSubscriptions();
  const createSubscription = useCreateSubscription();
  const sendTest = useSendTestNotification();
  const [countyFips, setCountyFips] = useState(defaultCountyFips ?? "");

  function handleSubscribe() {
    if (!countyFips.trim()) return;
    createSubscription.mutate({
      county_fips: countyFips.trim(),
      channel: "email",
      alert_types: ["flood", "weather"],
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Alert subscriptions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading ? <LoadingState label="Loading subscriptions…" /> : null}
        {isError ? (
          <ErrorState
            title="Failed to load subscriptions"
            description={error instanceof Error ? error.message : undefined}
            onRetry={() => refetch()}
          />
        ) : null}
        {!isLoading && !isError && data?.length === 0 ? (
          <EmptyState title="No subscriptions yet" />
        ) : null}
        <ul className="space-y-1">
          {data?.map((subscription) => (
            <li key={subscription.id} className="text-xs text-slate-300">
              {subscription.county_fips ?? subscription.property_id} via {subscription.channel}
            </li>
          ))}
        </ul>

        <div className="flex gap-2 pt-1">
          <Input
            value={countyFips}
            onChange={(event) => setCountyFips(event.target.value)}
            placeholder="County FIPS, e.g. 12103"
            aria-label="County FIPS for new subscription"
          />
          <Button size="sm" onClick={handleSubscribe} disabled={createSubscription.isPending}>
            Subscribe
          </Button>
        </div>
        {createSubscription.isError ? (
          <p className="text-[11px] text-red-400">
            {createSubscription.error instanceof Error
              ? createSubscription.error.message
              : "Failed to subscribe."}
          </p>
        ) : null}
      </CardContent>
      <CardFooter className="flex justify-end">
        <Button size="sm" variant="ghost" onClick={() => sendTest.mutate()} disabled={sendTest.isPending}>
          Send test notification
        </Button>
      </CardFooter>
    </Card>
  );
}
