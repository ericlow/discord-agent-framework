# Setting up Discord

Create the Discord server and application your agent will run in.

## 1. Create a Discord server

If you don't already have a server to add the agent to, create one. In the Discord
app, click the **+** button in the server list and follow the prompts.

Full instructions: <https://support.discord.com/hc/en-us/articles/204849977-How-do-I-create-a-server>

## 2. Create an application

Go to the Discord Developer Portal and click **New Application**, give it a name,
and open it:

<https://discord.com/developers/applications>

On the **General Information** page, copy two values — you'll need them later as
environment variables:

- **Application ID** → `DISCORD_APPLICATION_ID` (used to post responses and register
  the slash command)
- **Public Key** → `DISCORD_PUBLIC_KEY` (used to verify Discord's request signatures)

Save both into `infra/terraform.tfvars` (gitignored — never committed):

```hcl
discord_application_id = "your-application-id"
discord_public_key     = "your-public-key"
```

Copy `infra/terraform.tfvars.example` to `infra/terraform.tfvars` first if you
haven't. On deploy, Terraform sets these as the Lambda's environment variables.

## 3. Add a bot and copy its token

Open the **Bot** tab in the left sidebar. Discord creates the bot automatically with
the application, so there's nothing to add — you just need its token.

Click **Reset Token**, confirm, and copy the value. Discord shows the token only
once; if you lose it, reset again.

Save it to `infra/terraform.tfvars` — this one **is** a secret, so never commit or
share it:

```hcl
discord_bot_token = "your-bot-token"
```

You do **not** need to enable any Privileged Gateway Intents — this agent uses
Discord's HTTP interactions, not a gateway connection.

## 4. Invite the bot to your server

The bot posts its progress and answers as a member of your server, so it must be
invited in.

The quickest way is a direct install link. Take this URL and replace
`<application-id>` with your Application ID from step 2:

```
https://discord.com/oauth2/authorize?client_id=<application-id>&permissions=3072&scope=bot+applications.commands
```

- `scope=bot+applications.commands` — adds the bot and enables its slash command.
- `permissions=3072` — **View Channels** (1024) + **Send Messages** (2048), the only
  permissions this agent needs.

Open the link, choose your server, click **Authorize**, and complete the captcha.

> Alternatively, use the **OAuth2 → URL Generator** tab and select the same scopes
> and permissions by hand — it produces the same URL.

**Confirm the bot is in your server's member list** before continuing (open the
member panel on the right). Offline is fine — it responds over HTTP, not the gateway.
If it's not there, the authorization didn't complete; open the link again.

## 5. Get your server ID (for fast command registration)

Registering the slash command to a specific server is **instant**; global
registration takes up to ~1 hour. To register to your server, you need its ID.

Open your server in Discord and look at the URL:

```
https://discord.com/channels/<server-id>/<channel-id>
```

The first number is your **server (guild) ID**. Save it for the registration step
(run later, on your machine) in a gitignored `.env` at the repo root:

```
DISCORD_GUILD_ID=your-server-id
```

The channel ID is not needed — the agent reads the channel from each interaction.
