import type { LoaderFunctionArgs, HeadersFunction } from "react-router";
import { authenticate } from "../shopify.server";
import { boundary } from "@shopify/shopify-app-react-router/server";

export const loader = async ({ request }: LoaderFunctionArgs) => {
  await authenticate.admin(request);
  return null;
};

export default function Index() {
  return (
    <s-page heading="Vigil">
      <s-section heading="Order &amp; Fulfillment Watchdog">
        <s-paragraph>
          Vigil is installed and authenticated. Order detection, AI
          reasoning, and the approval dashboard get built here over the
          phases ahead.
        </s-paragraph>
      </s-section>

      <s-section slot="aside" heading="Status">
        <s-paragraph>
          <s-text>Scope: </s-text>read_orders
        </s-paragraph>
        <s-paragraph>
          <s-text>Phase: </s-text>1 — foundation
        </s-paragraph>
      </s-section>
    </s-page>
  );
}

export const headers: HeadersFunction = (headersArgs) => {
  return boundary.headers(headersArgs);
};