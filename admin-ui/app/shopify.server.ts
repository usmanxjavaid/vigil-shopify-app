import "@shopify/shopify-app-react-router/adapters/node";
import {
  ApiVersion,
  AppDistribution,
  shopifyApp,
} from "@shopify/shopify-app-react-router/server";
import { PrismaSessionStorage } from "@shopify/shopify-app-session-storage-prisma";
import prisma from "./db.server";

const shopify = shopifyApp({
  apiKey: process.env.SHOPIFY_API_KEY,
  apiSecretKey: process.env.SHOPIFY_API_SECRET || "",
  apiVersion: ApiVersion.July26,
  scopes: process.env.SCOPES?.split(","),
  appUrl: process.env.SHOPIFY_APP_URL || "",
  authPathPrefix: "/auth",
  sessionStorage: new PrismaSessionStorage(prisma),
  distribution: AppDistribution.AppStore,
  future: {
    expiringOfflineAccessTokens: true,
  },
  ...(process.env.SHOP_CUSTOM_DOMAIN
    ? { customShopDomains: [process.env.SHOP_CUSTOM_DOMAIN] }
    : {}),
});

// Pushes the current shop + access token to the Python backend's `shops`
// table. Fired on every authenticated admin request, not just at install —
// the "keep the token warm" design from the TAD, so background work later
// (webhooks, scheduled jobs) always has a recently-refreshed token.
async function syncShopToBackend(session: {
  shop: string;
  accessToken?: string;
  scope?: string;
}) {
  const backendUrl = process.env.PYTHON_BACKEND_URL;
  const internalSecret = process.env.INTERNAL_API_SECRET;

  if (!backendUrl || !internalSecret || !session.accessToken) {
    console.error("Shop sync skipped: missing backend config or access token");
    return;
  }

  try {
    const response = await fetch(`${backendUrl}/internal/shops/sync`, {
      method: "POST",
      headers: {
        "X-Internal-Secret": internalSecret,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        shop_domain: session.shop,
        access_token: session.accessToken,
        scope: session.scope ?? "",
      }),
    });

    if (!response.ok) {
      console.error(`Shop sync failed: ${response.status} ${await response.text()}`);
    }
  } catch (err) {
    // Never let a sync failure break the merchant's actual page load —
    // this is a side effect of authenticating, not the point of it.
    console.error("Shop sync error:", err);
  }
}

async function adminWithSync(
  ...args: Parameters<typeof shopify.authenticate.admin>
) {
  const result = await shopify.authenticate.admin(...args);
  await syncShopToBackend(result.session);
  return result;
}

export default shopify;
export const apiVersion = ApiVersion.July26;
export const addDocumentResponseHeaders = shopify.addDocumentResponseHeaders;
export const authenticate = {
  ...shopify.authenticate,
  admin: adminWithSync,
};
export const unauthenticated = shopify.unauthenticated;
export const login = shopify.login;
export const registerWebhooks = shopify.registerWebhooks;
export const sessionStorage = shopify.sessionStorage;