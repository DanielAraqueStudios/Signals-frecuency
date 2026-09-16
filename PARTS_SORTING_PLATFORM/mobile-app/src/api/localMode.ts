// Local-mode client: talks directly to LOCAL_MODE/local-server over
// plain HTTP on the shared WiFi access point -- no auth header, no
// api-gateway, no MQTT. See ../../../LOCAL_MODE/local-server/README.md.
//
// This is deliberately separate from ./client.ts / ./images.ts, which
// are cloud-mode's authenticated api-gateway client -- the two modes are
// independent deployments and this app can point at either, not both at
// once (see LOCAL_SERVER_URL below vs. API_GATEWAY_URL in ./config.ts).

export interface ClassificationResult {
  label: string;
  confidence: number | null;
  stub: boolean;
  reason?: string | null;
  features?: number[] | null;
}

// EDIT THIS (or wire to app config/extra, matching ./config.ts's
// pattern): local-server's LAN IP + port, e.g. "http://192.168.1.50:8100".
// There is no discovery mechanism in local mode.
export const LOCAL_SERVER_URL = "http://EDIT_THIS_LOCAL_SERVER_IP:8100";

function makeSampleId(): string {
  return `sample-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
}

export async function putImageLocal(
  uri: string,
  baseUrl: string = LOCAL_SERVER_URL
): Promise<ClassificationResult> {
  const sampleId = makeSampleId();
  const imageResponse = await fetch(uri);
  const imageBytes = await imageResponse.blob();

  const response = await fetch(`${baseUrl}/images/${sampleId}`, {
    method: "PUT",
    body: imageBytes,
  });

  if (!response.ok) {
    throw new Error(`Local-mode upload failed (${response.status})`);
  }
  return response.json();
}

export async function getLatestResultLocal(
  baseUrl: string = LOCAL_SERVER_URL
): Promise<ClassificationResult> {
  const response = await fetch(`${baseUrl}/images/latest`);
  if (!response.ok) {
    throw new Error(`Local-mode fetch failed (${response.status})`);
  }
  return response.json();
}
