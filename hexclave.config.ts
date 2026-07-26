import { defineHexclaveConfig } from "@hexclave/js";

export const config = defineHexclaveConfig({
  apps: {
    installed: {
      authentication: { enabled: true },
      teams: { enabled: true },
      rbac: { enabled: true },
      "api-keys": { enabled: true },
      analytics: { enabled: true },
    },
  },
  auth: {
    allowSignUp: true,
  },
  "auth.otp": {
    allowSignIn: true,
  },
  onboarding: {
    requireEmailVerification: true,
  },
  teams: {
    createPersonalTeamOnSignUp: false,
    allowClientTeamCreation: false,
  },
  rbac: {
    permissions: {
      view_events: {
        description: "View the team's Airlock security events",
        scope: "team",
      },
      manage_policies: {
        description: "Create and update the team's Airlock policies",
        scope: "team",
        containedPermissionIds: { view_events: true },
      },
      manage_api_keys: {
        description: "Create, list, and revoke the team's API keys",
        scope: "team",
      },
      team_admin: {
        description: "Administer the team's Airlock workspace",
        scope: "team",
        containedPermissionIds: {
          manage_policies: true,
          manage_api_keys: true,
        },
      },
    },
    defaultPermissions: {
      teamCreator: { team_admin: true },
      teamMember: { view_events: true },
      signUp: {},
    },
  },
  apiKeys: {
    enabled: {
      team: true,
      user: false,
    },
  },
});
