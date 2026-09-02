import type { ActionFunctionArgs, HeadersFunction, LoaderFunctionArgs } from "react-router";
import { useFetcher } from "react-router";
import { authenticate } from "../shopify.server";
import { boundary } from "@shopify/shopify-app-react-router/server";

export const loader = async ({ request }: LoaderFunctionArgs) => {
  await authenticate.admin(request);
  return null;
};

export const action = async ({ request }: ActionFunctionArgs) => {
  await authenticate.admin(request);

  const backendUrl = process.env.PYTHON_BACKEND_URL;
  const internalSecret = process.env.INTERNAL_API_SECRET;

  if (!backendUrl || !internalSecret) {
    return { error: "Backend not configured — check admin-ui/.env" };
  }

  try {
    const response = await fetch(`${backendUrl}/internal/test/orders`, {
      headers: { "X-Internal-Secret": internalSecret },
    });

    if (!response.ok) {
      const detail = await response.text();
      return { error: `Backend returned ${response.status}: ${detail}` };
    }

    return { data: await response.json() };
  } catch (err) {
    // Backend unreachable entirely — e.g. it crashed on boot, like just now.
    return { error: `Could not reach Python backend: ${String(err)}` };
  }
};

export default function Index() {
  const fetcher = useFetcher<typeof action>();
  const isLoading = fetcher.state !== "idle";
  const fetchOrders = () => fetcher.submit({}, { method: "POST" });

  return (
    <s-page heading="Vigil">
      <s-section heading="Order &amp; Fulfillment Watchdog">
        <s-paragraph>
          Vigil is installed and authenticated. Order detection, AI
          reasoning, and the approval dashboard get built here over the
          phases ahead.
        </s-paragraph>

        <s-button onClick={fetchOrders} {...(isLoading ? { loading: true } : {})}>
          Test: Fetch Orders via Python Backend
        </s-button>

        {fetcher.data?.error && <s-paragraph>Error: {fetcher.data.error}</s-paragraph>}

        {fetcher.data?.data && (
          <s-box padding="base" borderWidth="base" borderRadius="base" background="subdued">
            <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              <code>{JSON.stringify(fetcher.data.data, null, 2)}</code>
            </pre>
          </s-box>
        )}
      </s-section>

      <s-section slot="aside" heading="Status">
        <s-paragraph><s-text>Scope: </s-text>read_orders</s-paragraph>
        <s-paragraph><s-text>Phase: </s-text>2 — backend seam proof</s-paragraph>
      </s-section>
    </s-page>
  );
}

export const headers: HeadersFunction = (headersArgs) => {
  return boundary.headers(headersArgs);
};