"use client";

/**
 * useEventStream — Connects to the ForgeOS SSE stream and dispatches events.
 *
 * All frontend state is derived from this single event stream.
 */

import { useCallback, useRef } from "react";
import { getStreamUrl } from "@/services/api";
import type { ForgeOSEvent } from "@/types/events";

interface UseEventStreamOptions {
  onEvent: (event: ForgeOSEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

export function useEventStream({
  onEvent,
  onConnect,
  onDisconnect,
  onError,
}: UseEventStreamOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback((sessionId?: string) => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = getStreamUrl(sessionId);
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      onConnect?.();
    };

    eventSource.onmessage = (messageEvent) => {
      try {
        const data = JSON.parse(messageEvent.data) as ForgeOSEvent;
        onEvent(data);
        if (data.event === "completed") {
          eventSource.close();
          if (eventSourceRef.current === eventSource) {
            eventSourceRef.current = null;
            onDisconnect?.();
          }
        }
      } catch (e) {
        console.error("Failed to parse SSE event:", e);
      }
    };

    eventSource.onerror = () => {
      if (eventSourceRef.current !== eventSource) {
        return;
      }
      onError?.(new Error("SSE connection error"));
      if (eventSource.readyState === EventSource.CLOSED) {
        eventSourceRef.current = null;
        onDisconnect?.();
      }
    };
  }, [onEvent, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      onDisconnect?.();
    }
  }, [onDisconnect]);

  return { connect, disconnect };
}
