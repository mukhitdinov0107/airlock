import { HexclaveClientApp } from "@hexclave/js";

export const hexclaveClientApp = new HexclaveClientApp({
  tokenStore: "cookie",
  urls: {
    default: {
      type: "hosted",
    },
  },
});
