![EchoTuner Logo](./EchoTunerLogo.svg)

# EchoTuner - AI-Powered Playlist Generation Platform

EchoTuner is a tool for generating your personalized Spotify playlists based on audio features like energy, valence, danceability, and more. It started off as a fun idea for a simple public-facing app, but it quickly ran into the modern reality of building with Spotify's Web API.

As of 2025, Spotify has tightened the screws on public app access. With the new quota system and extended access rules, you now need over 250,000 monthly users, security audits, and formal review just to avoid your app getting throttled or locked to a 25-user limit. So… yeah. Public deployment? Not happening.

But here’s the twist: that limitation is exactly what makes EchoTuner worth open-sourcing.

Instead of chasing Spotify’s new “platform partner” dream, this project leans into the local development workflow. You run EchoTuner for yourself, with your own Spotify Developer OAuth credentials, in a local Docker container. That means no rate limits, no review process, no privacy weirdness, and total control over how you interact with your data. Just you, your playlists, and a dead-simple setup.

In fact, the "you have to run it yourself" part? That’s kind of the point. It encourages developers to spin up their own small-scale tools, explore the Spotify API on their terms, and stop relying on centralized services that might break or disappear overnight.

A self-contained music analysis tool you own completely? That's a win.

## Demo
There’s going to be a demo too - just not in the traditional sense. To comply with Spotify’s public app limitations, the demo strips out cross-device functionality like real-time playlist syncing across devices and user-specific storage. Instead, all data is saved locally in-session, and playlists are generated under a shared public sandbox account (not your real Spotify). Think of it as a staging area: playlists you create there are public and fully claimable with one click into your actual Spotify account.

So, whether you’re running it locally or poking around the demo, EchoTuner is here for curious developers who just want to understand their playlists - without needing a startup, a legal team, or a bunch of users.

## Documentation

Complete setup and usage documentation is available in the `docs/` directory:

**[Documentation Hub](docs/README.md)**

- **[API Documentation](docs/api/)** - Backend setup, configuration, and API reference
- **[App Documentation](docs/app/)** - Flutter app development and deployment  
- **[Quick Start Guides](docs/README.md)** - Get running in minutes


For detailed setup instructions, see the [Getting Started guide](docs/README.md).

## Project Philosophy

EchoTuner embraces the "run it yourself" philosophy. Instead of fighting Spotify's restrictive API quotas and review processes, we lean into local deployment. This approach gives you:

- **No Rate Limits** - Your Spotify developer credentials, your rules
- **Complete Privacy** - Your music data never leaves your infrastructure
- **Full Control** - Customize, modify, and extend however you want
- **No Dependencies** - No external services that can disappear or change terms, except for Spotify's API

This isn't just a music app - it's a template for building personal-scale software that you own completely.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
