import { useEffect, useState } from "react";
import { NetworkClient } from "../services/network";
import type { ConnectionStatus, InboundMessage } from "../types";

/**
 * Creates a single NetworkClient and exposes its messages + status as React state.
 * Stable for the lifetime of the component that mounts it.
 */
export function useNetwork() {
  const [client] = useState(() => new NetworkClient());
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [lastMessage, setLastMessage] = useState<InboundMessage | null>(null);

  useEffect(() => {
    client.onMessage(setLastMessage);
    client.onStatus((s) => setStatus(s as ConnectionStatus));
    client.connect();
    return () => {
      client.socket.close();
    };
  }, [client]);

  return { client, status, lastMessage };
}
