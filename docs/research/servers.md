# Public NetHack servers for an automated 3.6.7 run: Hardfought and NAO

Research for the claude-plays-nethack team, written 2026-09-26. The goal behind it: an LLM agent plays NetHack 3.6.7 over SSH and tries to ascend on a public server, so the result is on the public record.

**Method**
- Web only, over HTTPS: server websites, their public directory listings and xlogfiles, GitHub raw files for the server builds, and DNS-over-HTTPS. No SSH, telnet or raw TCP connection was made from this machine.
- I read the other team's harness read-only at `/home/user/kenforthewin/nethack_astra`, including `scripts/session.py`, `docs/SETUP.md`, `config/nethackrc`, `config/known_hosts`, `config/tmux.conf`, `memory/*.md` and `EVIDENCE.md`.
- I also downloaded their public evidence archive (`nethack-evidence.tar.gz` from release v1.0.0). Its SHA256 matched the published `73e7b580…`. I used it for these checks:
  - verbatim lobby screens;
  - server-side ttyrec timings;
  - SSH exit statuses around disconnects.
- Scratch copies are in the session scratchpad only.

**Tags**
- **[V]** Verified. The source is cited inline or listed under Sources. For the Astra material, "verified" means it was observed in their recorded screens, their ledger, or the server's ttyrecs.
- **[I]** My inference or recommendation. It is not stated by the server operators.
- **[U]** Unknown or unverified. Check it on the first login.

---

## 0. TL;DR: what changes our plan

1. **Hardfought is the only place to start a new 3.6.7 game.** NetHack 5.0.0 was released on 2026-05-02, and 3.7.0 was renamed to become it. [V]
   - **NAO** starts new games only in 5.0.0. 3.6.x is there only so players can finish old saves. [V]
   - **Hardfought** (US, EU and AU) still starts new 3.6.7 games. Its xlogfile shows new 3.6.7 games begun on 2026-09-25 and 2026-09-26. [V]
2. **Neither server publishes a bot or AI policy for ordinary play.** [V: none found]
   - TNNT, the November tournament hosted on Hardfought and run by the Hardfought admins, bans bots outright. [V]
   - Junethack explicitly allows bots. [V]
   - There is a direct precedent. An LLM agent, GPT 6 Astra playing as "CodexDelver", ascended in 3.6.7 on Hardfought US on 2026-09-21. The IRC bot Beholder announced it, it is listed on the public scoreboard, and I found no sign of any sanction. [V]
   - I recommend asking K2 or Tangles in #hardfought (Libera) before we start, and disclosing that the account is an AI. [I]
3. **Idle timeout on Hardfought: 30 minutes.** [V] It was measured four times, twice while in a game and twice in the lobby.
   - **In a game:** 1800 s with **no game output** triggers a SIGHUP, which makes NetHack hangup-save. SSH then exits with **status 7** (dgamelaunch's "Caught HUP"). `ServerAliveInterval` does not prevent this.
   - **In the lobby:** 1800 s with no input disconnects the lobby.
   - A hangup at a prompt **cancels the prompt**. That loses a wish or a genocide, and a hangup after offering the Amulet makes the game unwinnable. **The agent must never think for more than 30 minutes at a prompt.** [V: wiki; I: consequence]
4. **Login flow.** [V]
   - Run `ssh nethack@us.hardfought.org` on port 22. There is no SSH-level password. **Do not use plain `hardfought.org`:** since 2026-03-07 it points at Cloudflare.
   - Register or log in through dgamelaunch.
   - In the lobby, `p` = "Play last game", `r` = "Resume last save", and `1` = "NetHack (various versions)". The Astra notes say that `1` then `V` launched 3.6.7. [V for the lobby text; the submenu text is [U]]
5. **Hardfought defaults an automated player must override.** [V: server sysconf]
   - `number_pad:1`. `hjkl` do not move; `k` kicks.
   - `MSGTYPE=hide "Unknown command *"`. A mistyped key gives no feedback at all.
   - An `alert` MSGTYPE (a Hardfought patch) makes eel, kraken and couatl wrap messages wait for **TAB**. Space and Enter do not dismiss it.
   - In-game mail from spectators is enabled. That is a prompt-injection channel; turn it off with `OPTIONS=!mail`. [I]
6. **Records to expect.** [V]
   - Dumplogs are published immediately at `https://www.hardfought.org/userdata/<F>/<Name>/nethack/dumplog/<starttime>.nh.{txt,html}`.
   - ttyrecs go to S3 daily.
   - The xlogfile is `https://www.hardfought.org/xlogfiles/nethack36/xlogfile`, which nethackscoreboard.org reads.
   - The IRC bot Beholder announces the ascension, including a dumplog link.
   - The URLs move, so keep our own hashed copies. [V/I]
     - A ttyrec is uncompressed while it grows, becomes `.gz` when the session ends, and moves to S3 at the next daily 4:00am server-time run.
     - Dumplogs move to S3 after 30 days.

---

## 1. Connection methods

### 1.1 Hardfought (hdf-us, hdf-eu, hdf-au)

| Server | SSH command | Resolves to (DoH, 2026-09-26) | Web terminal |
|---|---|---|---|
| US (East Coast) | `ssh nethack@us.hardfought.org` (port 22) | 3.222.125.55 (AWS) | https://www.hardfought.org/hterm/ |
| EU (London) | `ssh nethack@eu.hardfought.org` | 18.134.185.165 | https://eu.hardfought.org/hterm/ |
| AU (Sydney) | `ssh nethack@au.hardfought.org` | 3.24.55.202 | https://au.hardfought.org/hterm/ |

**Connecting**
- [V] Hardfought's NetHack page says: "connect (ssh) to nethack@us.hardfought.org (US server, east coast), nethack@eu.hardfought.org (EU server, London), or to nethack@au.hardfought.org (AU server, Sydney) via port 22 (SSH)."
- [V] The home page notice reads: "Starting March 7th, 2026 at 3pm UTC, players accessing the hdf-us server via SSH must connect to **us.hardfought.org** instead of just hardfought.org."
  - `hardfought.org` and `www.hardfought.org` now resolve to Cloudflare (104.26.x.x, 172.67.75.47), which does not carry SSH.
  - Older docs still use the apex name and are stale: the NetHack Wiki DGLAUTH examples and the TNNT page.
- [V] **Telnet is not offered.** Only SSH and hterm are listed on the Hardfought pages and the wiki.
- [V] IPv6 works for SSH and HTTPS (NetHack Wiki "Hardfought", as of 2018).

**Accounts**
- [V] "Game account registration can *only* be done via SSH … ssh to nethack@us.hardfought.org and register your account there. Within a couple minutes, your registered account will sync with the other two servers (Europe and Australia)."
- [V] Each server keeps its own games and saves, which appear in separate xlogfiles and userdata trees.
- [V] **No SSH-level credential is needed.**
  - The site's instructions give only `ssh nethack@us.hardfought.org`, with no password.
  - The public-server list on the wiki notes passwords for the servers that need one; it notes none for Hardfought.
  - Astra's harness uses `PubkeyAuthentication=no` and has no SSH-password step, yet it lands straight in dgamelaunch.

**Published host key fingerprints** [V] (https://www.hardfought.org/nethack/)

| Server | Key | SHA256 | MD5 |
|---|---|---|---|
| Hardfought US | 3072 RSA | `SHA256:yya7aO81a5GlS4WN1D2xcQiAOh0EbnoEWsABy1NLkjw` | `MD5:fd:e6:e6:8c:25:4b:38:4c:b5:ac:1f:90:4c:de:53:35` |
| Hardfought US | 256 ECDSA | `SHA256:UmaLhglcKwjcrwtKC3gC0KhF99wj3ABJ+/2WH9n5MMk` | `MD5:03:bf:f5:29:b8:e6:ac:15:94:72:27:94:b8:06:2c:7b` |
| Hardfought US | 256 ED25519 | `SHA256:6I4FoeQJSX90yDFeWb7XTuq/AeuOFo2F2QEDSwgLWmY` | `MD5:30:3c:1e:bc:f1:33:bc:b1:a5:cc:49:e8:f0:4a:d8:24` |
| Hardfought EU | 3072 RSA | `SHA256:8NO9E2ZRd89qEcnIRGlui2ghi/CCPWpcgmAjBmFxPSI` | `MD5:72:5a:f9:fc:ef:d6:3d:09:34:09:dc:ed:7b:e7:5c:ea` |
| Hardfought EU | 256 ECDSA | `SHA256:dvFd57DrsekivUeY7MIiq3k8EsOlvrJbnLa3c21OkuQ` | `MD5:b7:eb:3d:32:29:c2:cc:8e:b9:a3:e1:8c:13:9e:93:2e` |
| Hardfought EU | 256 ED25519 | `SHA256:9Rud4+DZ+7oh4CCL3d1j9DPt+lSY7w9izISx0k509jk` | `MD5:16:2e:94:cf:ce:b2:8d:3c:86:f6:9f:45:18:55:7f:b2` |
| Hardfought AU | 2048 RSA | `SHA256:HsA6t2n4CJWvykszU/ICDM3VD44X0vfTrcZ0btD0K2c` | `MD5:b2:28:60:f7:09:dd:05:f8:1c:11:78:d1:e7:20:eb:5c` |
| Hardfought AU | 256 ECDSA | `SHA256:i3mOvo28VORw6Jh7mA2guqiEcNBoKEE3c+z2+idz8Yk` | `MD5:31:27:a2:b8:11:ae:f2:a4:6c:79:04:fd:e4:4c:77:13` |
| Hardfought AU | 256 ED25519 | `SHA256:txyepUIh66WAljPAcu70PER24AqlL0Lzd9LGssKDclc` | `MD5:33:dc:82:39:56:79:79:a4:d9:2f:5a:cc:04:b1:27:60` |

[V] The Astra harness pins this `known_hosts` line (`config/known_hosts`):

```
us.hardfought.org ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP+64+50p7Qjx4FOSlVpudjN6K/Pox47jXLTaygDxMdo
```

I hashed that key locally in Python. It gives `SHA256:6I4FoeQJSX90yDFeWb7XTuq/AeuOFo2F2QEDSwgLWmY` and `MD5:30:3c:1e:bc:…:d8:24`, which match the published US ED25519 fingerprint exactly. We can reuse the line, but should re-check it against the website before first use.

**The SSH invocation Astra used** [V] (`scripts/session.py`, `start()`, run inside a tmux pane):

```sh
ssh -F /dev/null -tt \
  -o UserKnownHostsFile=config/known_hosts -o GlobalKnownHostsFile=/dev/null \
  -o StrictHostKeyChecking=yes -o HostKeyAlgorithms=ssh-ed25519 \
  -o PubkeyAuthentication=no -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -o ConnectTimeout=15 nethack@us.hardfought.org
```

The tmux setup around it [V] (`config/tmux.conf`, `session.py`):
- Session size 144 columns × 36 rows, with `default-terminal screen-256color`, `status off` and `remain-on-exit on`.
- Tmux 3.6a crashed when `window-size manual` was set before the session existed. The workaround was to call `resize-window` after the session was created (`memory/session.md`).
- `remain-on-exit on` means a dropped connection shows as `Pane is dead (status N, <date>)`. That status is how they told the causes apart; see §5.

**Automatic login (optional)**
- [V] dgamelaunch reads `DGLAUTH=user:password` from the environment before `USER` and `LOGNAME` (Hardfought fork `dgamelaunch.c`).
- [V] The NetHack Wiki documents `ssh -o SetEnv=DGLAUTH=Name:Pass nethack@…`. This needs OpenSSH 7.8 or later.
- [V] The Hardfought fork's changelog (2.1.0-hdf) mentions "Fix $LASTGAME/$LASTSAVE not populating after SSH autologin".
- [I] That suggests Hardfought's sshd accepts DGLAUTH. It is not confirmed.
- [I] Typing credentials at the prompts is the known-good path; Astra did exactly that.

### 1.2 NAO (nethack.alt.org)

| Method | Command | Notes |
|---|---|---|
| SSH | `ssh nethack@nethack.alt.org` (the wiki also uses `ssh nethack@alt.org`) | Both names resolve to 66.45.8.102. `www.alt.org` is behind Cloudflare and is web only. |
| Telnet | `telnet nethack.alt.org` (port 23), or port **14321** | Plaintext. Avoid it; the password crosses the wire in the clear. |
| Web | https://www.alt.org/nethack/hterm/ | WebSocket; see §8. |

[V] The NAO home page (https://www.alt.org/nethack/) says: "To play NetHack on this server, just telnet nethack.alt.org (on normal port 23 or port 14321) or ssh nethack@nethack.alt.org."

**The host key changed on 2026-07-19** [V]: "NAO has moved to a new server, and the SSH host key has CHANGED … Verify against the [SSH fingerprints page]." Current fingerprints (https://www.alt.org/nethack/ssh_fingerprints.txt):

| Key | SHA256 | MD5 |
|---|---|---|
| 256 ECDSA | `SHA256:hI7uTptzHB+QalE9KnZuQNwNreuZaLiDozJkNrTUC0g` | `MD5:d7:0a:17:8c:32:d9:4f:7d:11:aa:fe:d1:69:6f:45:60` |
| 256 ED25519 | `SHA256:J8G6naZn9urmkqlJJIOlhuK2/1yiDje3Fp4gwseLQso` | `MD5:15:3c:78:a3:57:e8:ba:a0:b5:c1:a8:b2:a1:ae:71:26` |
| 3072 RSA | `SHA256:mJtJtQYkgbUU/bXqG6bmJcbe8x5MPX6Z3F2hsw2afNM` | `MD5:fb:16:03:79:e1:ae:81:a4:ac:3e:75:e6:db:e4:03:bb` |

The reference sshd config in the `altorg/nao-server` repo [V] (the repo says: "This does not necessarily reflect how NAO is configured currently"):
- `Match User nethack` with `PasswordAuthentication yes`, `PermitEmptyPasswords yes`, `PubkeyAuthentication no`, `AcceptEnv DGLAUTH`.
- In other words, the user `nethack` needs no password, and DGLAUTH autologin is accepted.
- The sample xinetd telnet config sets `rlimit_cpu = 600`. [I] It is one more reason to prefer SSH.

### 1.3 TERM and terminal size

- [V] `TERM`: Astra used `screen-256color` (tmux) successfully.
- [V] The dgamelaunch example config ships `default_term = "xterm"`, which is used when the client's TERM is unknown. [U] Hardfought's production value is not published.
- [V] The Hardfought banners use 256-color escapes.
- [V] **Minimum sizes:**
  - The Hardfought dgamelaunch fork (2.1.0-hdf): "Raise minimum terminal size to 40x15 to prevent curses crash".
  - NetHack's curses port panics below 15 rows × 40 columns (`win/curses/cursmain.c`).
  - The tty port needs 80×24 (COLNO=80, ROWNO+3=24). It is built with `CLIPPING`, so a smaller terminal scrolls the map instead of refusing to start.
- [I] Use at least **80×24 for tty**. For curses with `perm_invent`, go wider; Astra used **144×36**.
- [V] The window size is taken from the client, and the web client passes `?c=<cols>&l=<rows>`.
- [V] Curses draws its borders with DEC Special Graphics (`lqqqk` in raw ttyrecs). A screen parser must handle the `ESC ( 0` charset switch, or we avoid it by using `windowtype:tty` without DECgraphics.

### 1.4 What to use for an automated client [I]

**SSH in a persistent tmux pane (or a pty we own), to `us.hardfought.org`, with the pinned ED25519 key.** Astra already proved this works for a full ascension. On Hardfought, hterm is only needed if port 22 is blocked. Keep **one** long-lived session. Sessions of about 23.5 hours worked (§4.3).

---

## 2. dgamelaunch menu flow

### 2.1 Hardfought: the logged-in lobby, verbatim [V]

This was captured from the Astra ledger (`agent_observation`, 2026-09-10T11:56:15Z) on a 144-column terminal. Colors are stripped:

```
  ## Hardfought - public NetHack server - https://www.hardfought.org/
  ## join us at #hardfought on irc.libera.chat or #nethack-hardfought on Discord
  ## Logged in as: CodexDelver

  c) Change password      m) Change email
  s) Server information   j) Manage settings   w) Watch games in progress

     Play:
  1) NetHack (various versions)   p) Play last game   [nh367-hdf]
  2) 3.4.3 based variants         r) Resume last save [nh367-hdf]
  3) 3.6/5.0 based variants
  4) 4.x based variants
  5) Miscellaneous games

  t) TNNT Tournament: INACTIVE
  N) NetHackathon Tournament: INACTIVE

  MOTD (2026-09-06):
  NetHackathon Fall 2026: Sept 11th-13th
  https://nethackathon.org

  q) Quit =>
```

How the bracketed fields change:
- With no save file, the second bracket reads `r) Resume last save [none]`. This was observed at 2026-09-08T17:20:59Z.
- During NetHackathon weekends, the `N)` line reads `ACTIVE`.

What each lobby key does:

| Key | Action | Status |
|---|---|---|
| `p` | **Play last game** `[<game>]`. It launches whatever you played last; for us that is `nh367-hdf`. NetHack restores a save if one exists, otherwise it starts a new game. Astra started runs 2 and 3 this way. | [V] |
| `r` | **Resume last save** `[<game with newest save>]`. It shows "No saved game to resume." if there is none. | [V: label, and the dgl source `DGLCMD_RESUME_LAST`] |
| `1` | "NetHack (various versions)" submenu. Astra's notes record the batched keys **`1V`** as verified. After saving, dgl returned to that "version menu", and "To restore from that menu use uppercase `V`" (`memory/session.md`). So **`V` in submenu 1 = NetHack 3.6.7**. | [V: their notes; the submenu text itself is [U]] |
| `3` | "3.6/5.0 based variants". **Do not** pick a variant by mistake. | [V: label] |
| `t` | **TNNT.** This is a separate 3.6.7-based tournament game and it **bans bots**. Never press `t`. | [V] |
| `j` | "Manage settings". I believe it holds the rc editing, the editor preference and the rc sync (§2.4). | [V: label; contents [U]] |
| `w` | Watch games in progress. | [V] |
| `c` / `m` | Change password / change email. | [V: label] |
| `s` | Server information. | [V: label; contents [U]] |
| `q` | Quit. The dgl session ends, and so does SSH. | [V] |

`lastgame` marker [V]: `https://www.hardfought.org/userdata/C/CodexDelver/lastgame` contains `nh367`. The game's name as dgl reports it is `nh367-hdf`, which appears in the ttyrec header and the stale-process message.

### 2.2 The logged-out menu, login and registration (from dgamelaunch source)

[V] These strings come from the Hardfought fork `k21971/dgamelaunch` (`dgamelaunch.c`).
- NAO's `altorg/dgamelaunch` uses the same username, login and email strings.
- Its password prompt is different. It reads: `Please enter a password. Remember that this is sent over the net` / `in plaintext, so make it something new and expect it to be relatively` / `insecure.` / `20 character max. No ':' characters. Blank line to abort.`
- In NAO's code, a password containing `:` **terminates the session** (`graceful_exit(112)`). Use letters and digits only, 20 characters at most.
- [U] Neither server's production logged-out banner was captured, because Astra hid those screens for privacy.

**Logged-out menu.** The fork's example (`examples/dgl_menu_main_anon.txt`) and NAO's example both read: `l) Login`, `r) Register new user`, `w) Watch games in progress`, `q) Quit`, ending with the prompt `=>`. [I] Hardfought very probably uses the same keys. Astra's credential helper waited for a prompt containing "username" or "password", which matches the strings below.

**Login flow**

| Step | Screen text | You send |
|---|---|---|
| username | `Please enter your username. (blank entry aborts)` then `=> ` | name + Enter |
| password | `Please enter your password.` then `=> ` | password + Enter |

- A wrong password silently drops you back to the logged-out menu.
- A banned account shows `Sorry, that account has been banned.--More--`.

**Registration flow** (`r` on the logged-out menu)

| Step | Screen text | Rules |
|---|---|---|
| username | `Welcome new user. Please enter a username.` / `Only characters and numbers are allowed, with no spaces.` / `<N> character max.` / `=> ` | See the rules below this table. |
| password | `Please enter a password of up to 20 characters.` / `Blank line to abort.` / `=> ` / `And again:` / `=> ` | Mismatch: `Sorry, the passwords don't match. Try again.` |
| email | `Please enter your email address.` / `This is sent _nowhere_ but will be used if you ask the sysadmin for lost` / `password help. Please use a correct one. It only benefits you.` / `80 character max. No ':' characters. Blank line aborts.` / `=> ` | **Required.** A blank line aborts the whole registration, and the address must pass a syntax check. |

Username rules:
- Letters and digits only (`isalnum`), at least 2 characters.
- Uniqueness is case-insensitive (`collate nocase`).
- A bad entry shows `There was a problem with your last entry.`
- The production maximum is [U]. Observed name lengths go up to **16** characters on Hardfought and **15** on NAO 5.0, and every name in both xlogfiles is alphanumeric.

After registration you are logged in immediately. On Hardfought, the account syncs to EU and AU within minutes.

**Password reset** needs the username plus the registration email: https://www.hardfought.org/nethack/password-reset/ or https://www.alt.org/nethack/resetpw.php. [V]

**Choosing the account name** [I]. The dgl name becomes the character name. It appears in every public record: the dumplog, the xlogfile, Beholder announcements and the scoreboard. Pick a name that discloses automation, and never reuse `CodexDelver`.

### 2.3 Starting, playing, saving, resuming [V]

**What a new game shows**
- The ttyrec starts with a dgl header:

  ```
  Player: CodexDelver
  Game: nh367-hdf
  Server: $ATTR(172)Hardfought - public NetHack server$ATTR()
  Filename: 2026-09-06.18:44:41.260.ttyrec
  Time: (1788720281) Sun Sep  6 14:44:41 2026
  ```

  The time is server local time (EDT); the filename is UTC.
- Then the splash `NetHack, Copyright 1985-2026 … Version 3.6.7-1 Unix post-release, built May 23 11:43:56 2026.`
- Then `Shall I pick character's race, role, gender and alignment for you? [ynaq] (y)`.

**Saving** (curses): `S`, then `y`, then Space at the curses `>>`. That returns you to the dgl menu the game was launched from: the lobby for `p` and `r`, or the version submenu for `1V`.

**Resuming**: press `r` (or `p`) in the lobby, and the save restores directly. Astra verified this repeatedly, and every restore matched turn, HP and position.

**Game over**: after DYWYPI and the disclosure screens, the dumplog is written and dgl returns to the lobby. Astra's final notes on the ascension say "All disclosure menus completed, lobby no save."

### 2.4 Editing the rcfile

- [V] Hardfought's NetHack page: "either via the dgamelaunch menu before you start your game (options include using rnano or virus) or via the website here using the RC Editor page … Currently the RC Editor only works on the US-based server." EU and AU offer to sync the rc from US when you first log in there.
- [V] The web RC Editor (https://www.hardfought.org/nethack/rcedit/) lists **"NetHack 370-hdf"** and **"343-hdf"** editors, plus variants and TNNT. Its login page is titled "NetHack 3.7.x Login". **There is no 3.6.x entry.** So the 3.6.7 rc (`<Name>.nh36rc`) has to be edited through dgl, most likely under `j) Manage settings`. [I/U]
- [V] A 2020 Hardfought post says "You can also set your config editor preference, and there's a more robust system to transfer configs between servers and even between other players."
- [V] **The rc file is publicly readable**, for example https://www.hardfought.org/userdata/C/CodexDelver/nethack/CodexDelver.nh36rc. Astra verified its upload by comparing that file with the local copy.
  - [I] Use that URL to check every edit.
  - Never put anything secret in the rc.
- [V] **virus** is dgamelaunch's small vi clone. The template comment in `dgl-default-rcfile` says: "Type ESC a couple times, then ':q!' … to exit if you get stuck. To save, hit ESC and then ZZ or type ':wq'. To insert text, hit 'i'."
- [I, general nano knowledge] **rnano** is restricted GNU nano. `^O` then Enter saves, and `^X` exits (answer `Y` to save).
- [I] To automate the edit: open the editor, delete everything (virus: `1G` then `dG`; rnano: repeated `^K`), paste the whole rc in insert mode, save, and verify through the public URL. Test this by hand first.
- [V] NAO has a web editor at https://www.alt.org/nethack/webconf/ with "RC Edit 5.0.0" and "RC Edit 3.6.7" (raw edit). It asks for the NAO login, and "A default config file has to exist first … start a game first, save it, then come back."

### 2.5 Watching games [V]

This is the dgl help text from the fork's `examples/dgl_menu_watchmenu_help.txt`; [I] production is presumably the same:
- In the watch menu: `>`/`<` pages, `.`/`,` sort, `\` pauses auto-refresh, `a-zA-Z` picks a game, `*` picks a random one, and `q` returns.
- While watching: `q` goes back, **`m` sends mail to the player (requires login)**, `s` toggles charset stripping, and `r` resizes to the player's terminal.
- A second SSH session can watch your own game. Astra used this to confirm a frozen game on 2026-09-07.
- Who is online (Hardfought US) is visible over HTTPS at https://www.hardfought.org/nh/index.php.
- Near-live spectating over HTTPS also works: the growing ttyrec can be polled (§6).

---

## 3. Versions (as of 2026-09-26)

### 3.1 Official releases [V]

- **NetHack 5.0.0 was released on 2026-05-02.** nethack.org: "The NetHack DevTeam is announcing the release of NetHack 5.0.0 on May 2, 2026 … Existing saved games and bones files will not work with NetHack 5.0.0."
- It is the old 3.7.0. The NetHack Wiki: "3.7.0 … was never officially released … its source code was eventually used to produce a new major version, NetHack 5.0.0 … the version number was retired."
- **3.6.7** (released 2023-02-16) is the last 3.6.x release. The NetHack-3.6 git branch still receives post-release fixes. nethack.org posted a GCC 15 patch (2025-04-18) and fixed Windows 3.6.7 binaries (2025-07-02).
- So 3.6.7 is no longer "current". It is the previous series, still maintained for building.
- [I] Our local harness uses NLE, which is built on NetHack **3.6.6**. Gameplay differences from 3.6.7 are bug and security fixes only, but make sure the knowledge base does not assume NLE-specific rendering.

### 3.2 What Hardfought offers [V]

- **NetHack 3.6.7 (`nh367-hdf`)**
  - New games are allowed. The xlogfile https://www.hardfought.org/xlogfiles/nethack36/xlogfile has 48,051 games; the last 500 are all `version=3.6.7`; 11 were started after 2026-09-10, including new games on 2026-09-25 and 2026-09-26.
  - EU and AU also have recent 3.6.7 games.
  - The US 3.6 xlogfile records 24 ascensions ending after 2026-05-28. The most recent is CodexDelver's on 2026-09-21.
- **NetHack 5.0.0 (HDF build)**: `xlogfiles/nethack50`, 11,329 games since 2026-05-02.
- **NetHack 3.7.0**: `xlogfiles/nethack37`; games were still being started as of 2026-09-07. The wiki says that popular demand "allows NetHack 3.7.0 games to be finished out".
- **3.4.3-hdf, 1.3d**, many variants, **TNNT** (3.6.7-based) and **NetHackathon**. The dumplog and ttyrec index pages list these.
- The Hardfought home page describes the vanilla offering as the "latest developmental codebase, along with a couple older versions".

### 3.3 What NAO offers [V]

- The NAO site: "stock NetHack 5.0.0 (latest current version), or NetHack 3.6.1 - 3.6.7 depending on how old of a save you might have. NetHack 3.4.3 is no longer available for play here."
- The NetHack Wiki (nethack.alt.org): "Players with saved games of earlier versions (from NetHack 3.6.2 to NetHack 3.6.7 inclusive) may finish out their games, but **no player may start a new game with these versions**."
- The data agrees. Of NAO's 1,000 most recent games, 999 are 5.0.0; the single 3.6.7 game started on 2026-02-16 and finished on 2026-09-25.
- The NAO 3.6.7 build's dumplog header: `Unix NetHack Version 3.6.7-0 post-release - last build Sat Jul 18 03:16:38 2026 (87ff3781…,branch:master)`.
- The NAO 5.0.0 build's header: `Version 5.0.0-0 post-release … (3af73421…,branch:main)`.
- **Conclusion: NAO cannot host a new 3.6.7 attempt.**

### 3.4 Hardfought's 3.6.7 build compared with vanilla [V]

**Source and version strings**
- Source: https://github.com/k21971/NetHack36, branch `hardfought`. The repo description still says "3.6.3"; that is outdated.
- The HEAD commit is `8b4a575` (2026-05-23, "Fix: end of game curses mode bug"). It follows a merge of upstream `NetHack-3.6` the same day.
- The `#version` and dumplog first line read exactly:
  `Unix NetHack Version 3.6.7-1 post-release - last build Sat May 23 11:43:56 2026 (8b4a575d7e9df6eacf187bfed899886b4b79e5f6,branch:hardfought).`
- The curses splash reads `Version 3.6.7-1 Unix post-release, built May 23 11:43:56 2026.`

**Compile-time additions** (`sys/unix/hints/hardfought`)
- `CURSES_GRAPHICS`, alongside tty. **The default windowtype is still tty.**
- `TIMED_DELAY`.
- `TTY_TILES_ESCCODES`, which enables `vt_tiledata`.
- `EDIT_GETLIN`.
- `SCORE_ON_BOTL`, so the `showscore` option works.
- `DGAMELAUNCH`, which adds:
  - the extrainfo file for the watch list;
  - the whereis file;
  - `MAILCKFREQ 5` with `SIMPLE_MAIL` (in-game mail from dgl);
  - `LIVELOG_ENABLE`.
- `DUMPLOG` plus `DUMPHTML`.
- `DLB`, gzip-compressed saves, and `INSURANCE`.
- The chroot is at `/nh367-hdf`; the lock directory is `/dgldir/inprogress-nh367-hdf`.

**Option set**: identical to vanilla 3.6's option table except for one addition, a MSGTYPE value **`alert`** ("Force acknowlegement with <TAB>"). tty prints ` <TAB>` and waits only for `\t`; curses prints `<TAB>` and loops until TAB (`win/tty/topl.c`, `win/curses/cursmesg.c`).

**The sysconf** (server-wide defaults applied **before** the user's rc; `sys/unix/sysconf`, copied into the chroot by `install-to-chroot.sh`):

```
WIZARDS=root games
EXPLORERS=*
CHECK_PLNAME=1
MAXPLAYERS=0
SUPPORT=Contact K2 or Tangles on Libera irc channel #hardfought
RECOVER=Run the recover program.
ACCESSIBILITY=1
PERSMAX=50
ENTRYMAX=2000
POINTSMIN=1
LIVELOG=0x0FFF
LLC_TURNS=3000
DUMPLOGFILE=/dgldir/userdata/%N/%n/nethack/dumplog/%t.nh.txt
DUMPHTMLFILE=/dgldir/userdata/%N/%n/nethack/dumplog/%t.nh.html
PANICTRACE_GDB=1
PANICTRACE_LIBC=2
OPTIONS=disclose:yi ya yv yg yc yo
OPTIONS=bones,color,lit_corridor,dark_room,autodig,autoopen
OPTIONS=boulder:0,pickup_burden:unencumbered
OPTIONS=!autopickup,hilite_pet,hilite_pile,time,use_darkgray
OPTIONS=msg_window:reversed,number_pad:1,sortloot:full
OPTIONS=menu_objsyms,perm_invent,hitpointbar
MSGTYPE=hide "Unknown command *"
MSGTYPE=alert "The (couatl|.*eel|kraken) swings itself around you!"
```

**Dumplog format**: the standard 3.6 dumplog, which includes a "Latest messages" section, the inventory and bag contents, attributes, vanquished monsters, genocided monsters, voluntary challenges, the dungeon overview and the final farewell block. There is also an HTML twin (`NHdump.css`). The file name is the **game start time** in Unix epoch seconds, for example `1788964024.nh.txt` for a game begun at 2026-09-09 14:27:04 UTC.

---

## 4. Policies

### 4.1 Bots, AI and automated play

**Found:**
- **Hardfought, general play: no published rule.** [V] Checked: the home page, the NetHack page, the RC Editor, the hterm and tournament pages, and a forum index scan.
  - The only operational policy text is about crashes and account registration.
  - The sysconf `SUPPORT` line names K2 and Tangles in #hardfought.
- **NAO, general play: no published rule.** [V] Checked: the home page, news, `naonh.php` and `webconf`.
- **TNNT** (November; hosted on Hardfought; K2 and Tangles are on its team) [V], from https://tnnt.org/faq:
  > "Bots are prohibited. TNNT is a tournament for human players, not a competition for the best or luckiest bot. Players found to be running a bot may be summarily banned from the tournament. Our working definition of a bot is any system that automatically evaluates game state and makes gameplay decisions."

  Also: "don't deliberately corrupt or leak memory or otherwise try to crash or hang up the game." An LLM agent is a bot by this definition. **Never launch the `t) TNNT` game.**
- **Junethack** (June, cross-server; most variants hosted on Hardfought) [V], from https://junethack.net/rules:
  > "Feel free to: … use NetHack playing bots or so called "augmentation" tools like Interhack. … make multiple accounts."

  It also says "Please don't: … use disconnection at critical spots to hide a death from logs." Junethack 2026 ran June 1–30, so the next one is June 2027.

**Precedent:**
- [V] CodexDelver, an LLM agent, played 3.6.7 on Hardfought US from 2026-09-06 to 2026-09-21 and ascended.
- Beholder announced it in #hardfought: `[hdf-us] [nh367] CodexDelver (Val Dwa Fem Law), 1766446 points, T:37140, ascended`, followed by the dumplog link.
- One user replied `^ LLM`. That is the only reaction in that day's log.
- It is on nethackscoreboard.org's vanilla ascension list.
- The #hardfought logs contain **no admin statement** on AI or bot players either way. I searched them through Hardfought's log browser, whose global search covers the whole archive, for "LLM", "bots", "GPT", "Codex", "Astra" and "CodexDelver", and read the matching lines in context.
  - The community mentions are neutral chatter:
    - 2026-06-11: "are people letting LLM bots loose in here or what";
    - 2026-09-23: Beholder relayed the Reddit post "An LLM (Astra) Ascended NetHack";
    - 2026-09-24: "NetHackers - trying to build a bot that can ascend reliably".
  - One etiquette point came up. On 2026-05-03 ais523 obfuscated the xlogfile URL "to stop LLM scrapers noticing a URL and visiting what will eventually be a very large page incessantly".
  - [I] Our monitoring should read large xlogfile and livelog files with HTTP Range requests (tail only) and poll them rarely.
- [V] Historically, bots have run on public servers: BotHack targeted NAO ("thanks … to FIQ for running the bot on the nethack.alt.org server"), and its first ascension (smartbot3, 2015) was on acehack.de/xd.cm.

**Recommendation [I]:**
- Before playing, ask in #hardfought (Libera, or Discord #nethack-hardfought) or email admin@hardfought.org.
- Put the automation disclosure in the account name and the plan.
- Stay away from tournament games.
- Behave like a courteous human client: one game at a time, no reconnect storms, `!bones` if dying repeatedly on bones-eligible levels (TNNT's courtesy note).

### 4.2 Idle timeouts

**Hardfought: 1800 seconds (30 minutes) of inactivity, both in-game and in the lobby.** [V] These are the measurements from the Astra evidence:

| When (UTC) | Where | Last activity to disconnect | SSH exit | Outcome |
|---|---|---|---|---|
| 2026-09-10 11:56:14 to 12:26:14 | lobby after a save | **1800.0 s** after the last output | status 7 | nothing lost (already saved) |
| 2026-09-14 11:54:12 to 12:24:12 | lobby after a save | **1800.0 s** | status 7 | nothing lost |
| 2026-09-20 15:17:48 to 15:47:48 | **in game**, waiting on a human approval | server ttyrec gap **1800.000 s** | status 7 | hangup-save; resumed with `r`, same turn (T26986) |
| 2026-09-20 19:47:20 to 20:17:20 | **in game, bag menu open** | server ttyrec gap **1800.000 s** | status 7 | hangup-save; resumed with `r`, same state (T28520) |

**Mechanism (Hardfought fork source)** [V]:
- `ttyrec.c:dooutput()` re-arms `alarm(max_idle_time)` every time the **game produces output**.
- When the alarm fires, `game_idle_kill()` sends SIGHUP to the game and to the dgl parent.
- `catch_sighup()` then calls `graceful_exit(7)`, and the README's error table says "7 Caught HUP".
- The lobby has a separate `menu_max_idle_time` alarm. Its default is 0 (off); the measured value is 1800.

**Consequences:**
- [V] SSH keepalives (`ServerAliveInterval=30`, as Astra used) **do not reset this timer**. The Astra data shows disconnects at exactly 1800 s despite them.
- [I] Any key that makes the game redraw resets it. `^R` (redraw) is free in game time.
- [I] A keystroke that produces **no output** may not reset the timer. Unknown commands are hidden by the sysconf `MSGTYPE=hide`.
- [I] Do not send keep-alives while inside a text prompt such as "For what do you wish?"; they may type into it.
- [I] Decide wishes and genocides *before* triggering them.
- [V] The NetHack Wiki "Hangup" page:
  > "Beware of hanging up during a prompt, as it has the effect of cancelling the prompt. You will not get a refund on your wish or genocide order. If a hangup is triggered after offering the Amulet of Yendor on the Astral Plane but before ascending, you will render the game unwinnable."

**NAO: no published value.** [U] The dgamelaunch default is off, and NAO's production config is not public.

### 4.3 Maximum session length, rate limits, multiple connections

- **No published maximum session length.** [V: none found] Astra's single ttyrecs, each one continuous SSH session, ran about **23.5 hours** (2026-09-20 20:36 to 2026-09-21 20:08 UTC) and about 20.7 hours (2026-09-08 17:42 to 2026-09-09 14:25). [V]
- **No published rate limits.** [V: none found]
  - [V] The Hardfought dgamelaunch fork has "comprehensive IP address logging", including failed logins (changelog 2.0.0-hdf).
  - [I] Avoid tight reconnect loops and repeated failed logins.
- **Multiple simultaneous connections with the same account are possible.** [V] Astra held a second SSH session in the lobby, watching its own frozen game, while the game connection hung (2026-09-07).
- **You cannot run the same game twice.** [V] Launching `nh367-hdf` while another process holds it triggers dgl's stale-process takeover (§5), which SIGHUPs the other instance.
- [V] TNNT's FAQ notes that one account may run games on different Hardfought servers at the same time; that is a tournament context.
- **Account naming rules**: alphanumeric only, at least 2 characters, a maximum length of [U] (16 observed on Hardfought), and case-insensitive uniqueness. [V] No other published naming policy.

---

## 5. Disconnects, recovery and pitfalls

### 5.1 What happens on disconnect [V]

- **If SSH drops**, sshd sends SIGHUP. dgamelaunch's `catch_sighup()` waits 10 s, sends SIGHUP to the game, waits 5 s and exits. NetHack's hangup handler saves the game.
- **Reconnecting**: log in again and press `r` (Resume last save) or `p`. Astra did this after each of the five incidents in §5.2, and every time the exact turn, HP and position were restored.
- **If the old game process is still running** (network drop, frozen client), launching the game again shows:

  ```
  ## Hardfought - public NetHack server - https://www.hardfought.org/

   There are some stale nh367-hdf processes, will recover in 9   seconds.
   Press a key NOW if you don't want this to happen!
  ```

  - This was captured on 2026-09-14 at 03:45:33 UTC, 52 s after an SSH drop with status 255.
  - **Pressing any key aborts the recovery.** Send nothing for about 15 s.
  - dgl then SIGHUPs the old process, waits up to 10 s, and if needed asks `Force its termination? [yn]`.
  - Then it launches, and the save restores.
- **If NetHack itself finds a lock held by a live process**, it asks `There is already a game in progress under your name.  Destroy old game? [yn]` (`sys/unix/unixunix.c`). **Always answer `n`.** `y` erases the in-progress level files.
- **If the old process is dead but its lock exists** (a crash), NetHack **silently erases the old locks and starts fresh**. This is `veryold()`: the pid no longer exists, so it calls `eraseoldlocks()`. Hence the operators' warnings below. [V: source; I: interpretation]
  - Hardfought: "Try NOT to start a new game or, if given the option, to destroy your old game if you want the chance for it to be recovered. Contact the admins with your crash report … Turnaround time will typically be within 24 hours."
  - NAO: "If you simply lost connection … the server will attempt an auto-recover of your game after 30 minutes. Do NOT start a new game or have the server destroy the current game."
- **Hardfought keeps backup saves**, and admins restore or roll back on request. [V] In #hardfought on 2026-06-11, when a save was corrupted, K2 said: "last immediate backup save is from june 9th right before midnight EDT … you either roll back to the older backup save … or start a new game". On 2026-02-16, after an outage, K2 said "all 370-hdf games recovered".
  - [I] A rollback would show up in the ttyrecs. For a clean public record, avoid needing one.

### 5.2 Incidents in the Astra run [V]

| UTC | Symptom | Exit | Recovery |
|---|---|---|---|
| 2026-09-07 ~05:35 | Game frozen. Keys did nothing, the spectator view was frozen on the same turn, and the lobby was reachable from a second session. | client killed with `~.` | reconnected, logged in, `r`: "same save restored at T15474", "no admin contact needed" |
| 2026-09-08 ~03:30 | SSH pane dead; cause not recorded | ? | `r`, same save (T28421) |
| 2026-09-14 03:44:41 | Network drop, 18 s after the last input | 255 | `p`, stale-process countdown, restored T22734 |
| 2026-09-20 15:47:46 | Idle HUP (§4.2) | 7 | `r` |
| 2026-09-20 20:17:18 | Idle HUP with a bag menu open | 7 | `r`, exact state restored |

### 5.3 Safe reconnect procedure [I]

1. Reconnect and log in.
2. Read the lobby.
   - If it shows `r) Resume last save [nh367-hdf]`, press `r`.
3. If it shows `[none]` but we believe a game is in progress, first confirm the game is *still running*. Check https://www.hardfought.org/nh/index.php (players online) or the `w` watch list.
   - If the game is listed, press `p` and **send nothing** until the countdown finishes.
   - If it is not listed (the process is dead, so this was a crash), **do not press `p`**. Stop and contact the admins.
4. On `Destroy old game?`, answer `n`.
5. If the character-selection prompt appears when we expected a restore, stop. Do not proceed.

### 5.4 Other pitfalls

- **`number_pad:1` is the server default.** [V: sysconf; Astra: "`k` opened a kick prompt"] Set `number_pad:0` for vi-keys, or use digits consistently. Watch for count prefixes: with number_pad, counts need `n`. Astra's run-3 journal line 1552 records: "ERROR33225: sent literal10s intending searchcount, forgot numpad requires n".
- **Unknown commands are silent** (`MSGTYPE=hide "Unknown command *"`). [V] Override it with `MSGTYPE=show "Unknown command"` in our rc. [I] User MSGTYPE entries are prepended and matched first (`msgtype_add` and `msgtype_type` in `options.c`), so ours win.
- **The TAB-only `alert`** for `The (couatl|.*eel|kraken) swings itself around you!`. [V] Either handle `<TAB>` in the harness, or override it with `MSGTYPE=stop "The (couatl|.*eel|kraken) swings itself around you!"`. [I]
- **In-game mail** (`MAIL` + `SIMPLE_MAIL`) [V].
  - Any logged-in spectator can press `m` in watch mode to mail us.
  - A mail daemon then delivers a scroll whose text is "This message is from '<user>'. It reads: "<text>"."
  - [I] That is arbitrary third-party text entering the agent's context, a prompt-injection vector. Use `OPTIONS=!mail`, and treat any mail text as untrusted data.
- **Arrow keys and escape sequences.** [V] Astra: "Named Up produced an unintended take-off menu (escape sequence interpreted incorrectly); avoid arrow keys." Send literal game keys only.
- **tmux and `;`.** [V] `tmux send-keys ';'` is parsed as a command separator. Astra sends the byte with `send-keys -H 3b`.
- **Hangup-save exploits.** [I] Junethack forbids "disconnection at critical spots to hide a death", and TNNT forbids trying to "hang up the game". Never disconnect on purpose mid-danger. The record should show clean saves: `S`, `y`, Space.
- **Server-time dependencies.** [V] The server clock is US Eastern (Beholder's `!time` reports "EST"; the ttyrec headers are EDT). [I] Moon phase, Friday the 13th and night-time effects follow that clock. Astra saw a "New-moon warning on restore".
- **Cloudflare on the web front ends.** [V] Some NAO pages (`plr.php`, `dumplogs.php`, `browsettyrec.php`) return a JavaScript challenge to scripts (HTTP 403 "Just a moment…"). The userdata directory listings and files are directly fetchable on both sites.

---

## 6. Public records

### 6.1 Hardfought URL patterns [V: all example URLs fetched on 2026-09-26]

| Record | Pattern | Example |
|---|---|---|
| Userdata directory | `https://www.hardfought.org/userdata/<F>/<Name>/nethack/`, where `<F>` is the first character of the name, case-sensitive | https://www.hardfought.org/userdata/C/CodexDelver/nethack/ |
| Dumplog (text and HTML), about 30 days on the server | `…/userdata/<F>/<Name>/nethack/dumplog/<starttime>.nh.txt` and `.nh.html` | https://www.hardfought.org/userdata/C/CodexDelver/nethack/dumplog/1788964024.nh.txt |
| Dumplog after archiving | `https://hdf-us.s3.amazonaws.com/dumplogs/<f>/<Name>/nethack/dumplog/<starttime>.nh.txt` | https://hdf-us.s3.amazonaws.com/dumplogs/s/spazm/nethack/dumplog/1782496227.nh.txt |
| Dumplog browser | `https://www.hardfought.org/nh/nethack/browsedumplog-us.php?player=<Name>` | https://www.hardfought.org/nh/nethack/browsedumplog-us.php?player=CodexDelver |
| ttyrec while in progress, or less than a day old | `…/userdata/<F>/<Name>/nethack/ttyrec/<YYYY-MM-DD.HH:MM:SS.mmm>.ttyrec` (UTC). It grows while you play and becomes `.ttyrec.gz` when the session ends; the uncompressed URL then 404s. | (Astra's `EVIDENCE.md` notes the 404 on the uncompressed URL.) |
| ttyrec archive (S3, moved daily) | `https://hdf-us.s3.amazonaws.com/ttyrec/<F>/<Name>/nethack/<stamp>.ttyrec.gz` | https://hdf-us.s3.amazonaws.com/ttyrec/C/CodexDelver/nethack/2026-09-20.20:36:00.735.ttyrec.gz |
| ttyrec browser and web player | `https://www.hardfought.org/nh/nethack/browsettyrec-us.php?player=<Name>`, which links to `trd-us/?file=<S3 url>` | https://www.hardfought.org/nh/nethack/browsettyrec-us.php?player=CodexDelver |
| rc file (public) | `…/userdata/<F>/<Name>/nethack/<Name>.nh36rc` | https://www.hardfought.org/userdata/C/CodexDelver/nethack/CodexDelver.nh36rc |
| xlogfile (3.6.x) | https://www.hardfought.org/xlogfiles/nethack36/xlogfile | EU and AU: `https://eu.hardfought.org/xlogfiles/nethack36/xlogfile`, and the same path on `au.` |
| livelog (3.6.x) | https://www.hardfought.org/xlogfiles/nethack36/livelog | Records wishes, uniques killed, achievements, crowning and so on. |
| Scoreboard | https://nethackscoreboard.org/ascended.nh.html and `https://nethackscoreboard.org/players/<F>/<Name>.nh.html` | https://nethackscoreboard.org/players/C/CodexDelver.nh.html |
| IRC announcements | Beholder in #hardfought (Libera). Logs are searchable at https://www.hardfought.org/nethack/irclogs/ | |
| Players online (US) | https://www.hardfought.org/nh/index.php | |

**Archive schedules** [V]
- ttyrecs: "The ttyrec archive schedule runs once per day at 4:00am local server time … moved … to an AWS S3 bucket." The S3 `Last-Modified` for CodexDelver's 2026-09-06 ttyrec is 2026-09-07 08:00:23 GMT.
- dumplogs: "runs once per day at 4:30am local server time … All dumplogs 30 days old or newer remain located on the local server … Anything older is archived."

[I] **For the record, keep our own copies.** The scoreboard links point at the `www.hardfought.org/userdata/…` dumplog URL, which moves to S3 after 30 days. Astra hashed and kept every dumplog and ttyrec segment as soon as it was published, and we should too.

### 6.2 How an ascension looks in each record [V, CodexDelver]

- **xlogfile**:

  ```
  version=3.6.7 points=1766446 deathdnum=7 deathlev=-5 maxlvl=52 hp=35 maxhp=200 deaths=0 … name=CodexDelver death=ascended conduct=0x480 turns=37140 achieve=0xfff … starttime=1788964024 endtime=1790021082 … flags=0x0
  ```

  The fields are tab-separated.
- **dumplog tail**: `Farvel CodexDelver the Demigoddess...` / `You went to your reward with 1766446 points,` / … / `You were level 19 with a maximum of 200 hit points when you ascended.`
- **Beholder**: `[hdf-us] [nh367] CodexDelver (Val Dwa Fem Law), 1766446 points, T:37140, ascended`, followed by the dumplog `.nh.html` URL.
- **Livelog** entries during the game: `entered the Planes`, `wished for "…"`, `killed the Wizard of Yendor`, `performed the invocation`, `acquired the Amulet of Yendor`, and so on.
- **Scoreboard**: a row in `ascended.nh.html` with `3.6.7`, the name, the role/race/gender/alignment, the points (linked to the dumplog), turns, realtime and more.

### 6.3 NAO URL patterns [V]

- Dumplog: `https://www.alt.org/nethack/userdata/<f>/<Name>/dumplog/<starttime>.nh<ver>.txt`, where `<ver>` is `500` for 5.0.0 or `367` for 3.6.7. Example: https://www.alt.org/nethack/userdata/p/pakka/dumplog/1790282377.nh500.txt
  - Older files redirect to `https://archive.alt.org/dumplog/<Name>/<file>`.
- ttyrec: `…/userdata/<f>/<Name>/ttyrec/<YYYY-MM-DD.HH:MM:SS.mmm>.ttyrec`. rc files: `<Name>.nh500rc` and `<Name>.nh367rc`.
- xlogfiles: https://www.alt.org/nethack/xlogfile.nh500 and https://www.alt.org/nethack/xlogfile.nh363+ (3.6.3–3.6.7).
- Bulk archives: https://archive.alt.org/archive/index.html.
- IRC: Rodney in #nethack (Libera).

### 6.4 Tournaments

- **Junethack** (https://junethack.net/): June, cross-server, and bots are allowed [V]. Its FAQ is at https://nethackwiki.com/wiki/Junethack/FAQ.
- **TNNT** (https://tnnt.org/): all of November, on Hardfought, 3.6.7-based ("core gameplay unaffected"), **bots prohibited**. [V]
- **NetHackathon** (https://nethackathon.org/): April and September. Streamers share one account. [V: Hardfought tournaments page]

---

## 7. rcfile: server defaults and a recommendation

### 7.1 Server defaults

- [V] The sysconf `OPTIONS` in §3.4 apply to everyone before the user's rc.
- [U] The per-user rc template that dgl copies on first edit is not public.
- [I] Astra's rc comment "Retain the shakedown's gameplay/input defaults: number_pad:1,!autopickup,autodig,fruit:slime mold,boulder:0" matches the fork's generic `dgl-default-rcfile` template (`OPTIONS=showexp,showscore,time,color,!autopickup` / `OPTIONS=autodig,fruit:slime mold,boulder:0`) combined with the sysconf.
- Astra's final rc for reference (`config/nethackrc`, identical to the public `CodexDelver.nh36rc`):
  - `windowtype:curses`, `windowborders:2`, `perm_invent`;
  - colors, `menucolors`, `hilite_pet`, `hilite_pile`;
  - `showexp`, `showscore`, `time`, `hitpointbar`, `statushilites:10`;
  - `number_pad:1`, `!autopickup`, `autodig`, `boulder:0`;
  - `msg_window:reversed`, `msghistory:60`;
  - plus HILITE_STATUS and MENUCOLOR lines.

### 7.2 Are the options we want supported in this build?

[V] Every option asked about exists in the Hardfought 3.6.7 option table (`src/options.c`, branch `hardfought`):

| Option | Supported | Note |
|---|---|---|
| `windowtype:tty` / `curses` | yes | Both are compiled in; the default is tty. |
| `number_pad` | yes | The server default is 1. |
| `paranoid_confirmation` | yes | Values: `Confirm quit die bones attack wand-break eat Were-change pray Remove`. |
| `runmode` | yes | `teleport`, `run` (the default), `walk`, `crawl`. |
| `timed_delay` | yes | `TIMED_DELAY` is compiled in. |
| `autopickup` / `pickup_types` | yes | The sysconf sets `!autopickup`. |
| `disclose` | yes | The sysconf sets `yi ya yv yg yc yo`. |
| `menucolors`, `hilite_pet`, `hilite_pile` | yes | |
| `boulder` | yes | Marked deprecated in favour of `S_boulder`; the sysconf sets `boulder:0`. |
| `time`, `showexp`, `showscore` | yes | `showscore` needs `SCORE_ON_BOTL`, which is compiled in. |
| `mention_walls` | yes | |
| `mail` | yes | Turn it off (§5.4). |
| `perm_invent`, `hitpointbar`, `statushilites`, `sortloot`, `vt_tiledata`, `whatis_coord`, `herecmd_menu`, `force_invmenu` | yes | |

### 7.3 A suggested starting rc for an automated player [I]

This is untested; review it against our parser.

```
OPTIONS=windowtype:tty,!timed_delay,runmode:teleport
OPTIONS=number_pad:0
OPTIONS=autopickup,pickup_types:$
OPTIONS=paranoid_confirmation:Confirm quit die attack pray wand-break Were-change Remove
OPTIONS=disclose:+i +a +v +g +c +o
OPTIONS=time,showexp,showscore,mention_walls,!mail
OPTIONS=msg_window:full,msghistory:100
OPTIONS=!perm_invent
MSGTYPE=show "Unknown command"
MSGTYPE=stop "The (couatl|.*eel|kraken) swings itself around you!"
```

Why these choices:
- **`number_pad:0`** gives vi-keys, which matches the NLE command vocabulary the gamer already knows.
- **`!perm_invent`** and **tty** keep the 80×24 layout close to NLE.
- **`runmode:teleport`** and **`!timed_delay`** mean fewer intermediate frames to parse.
- **`autopickup` with `pickup_types:$`** picks up gold only. Use `!autopickup` if we want every pickup to be explicit.
- **`!mail`** blocks third-party text.
- The **two MSGTYPE lines** undo the silent unknown-command default and the TAB-only alert.
- Things to decide deliberately: the `boulder` symbol (the sysconf's `0` versus NLE's `` ` ``) and whether to keep `bones` on.

---

## 8. Web-based play (HTTPS)

**Hardfought "hterm"** [V]
- Pages: https://www.hardfought.org/nethack/hterm/, then `hterm-us`, `-eu`, `-au`. These embed `https://<host>/hterm/`, titled "Hardfought Web Term".
- Hardfought: "Using hterm allows you to [play] by loading the game via your web browser."
- **Protocol** (`/hterm/wstty.js`):
  - A browser WebSocket to **`wss://<host>/ws-hterm?c=<cols>&l=<rows>`** with `binaryType = "arraybuffer"`.
  - Keystrokes are sent as raw bytes (`Uint8Array`), and server output arrives as binary frames written as UTF-8.
  - The terminal emulator is Chromium's hterm (1.92.1+), with `terminal-encoding` set to `iso-2022` so NetHack line drawing works.
  - The page's own "c) Connect" menu is client-side. After connecting you land in the same dgamelaunch lobby.
- www.hardfought.org sits behind Cloudflare; a comment in `wstty.js` says so. `eu.` and `au.` resolve directly to AWS.

**NAO** [V]
- https://www.alt.org/nethack/hterm/ ("Implemented NAO Web Player using hterm and kerio's wstty", 2015).
- The WebSocket is **`wss://www.alt.org/wstty-wss?c=<cols>&l=<rows>`**, the same framing, behind Cloudflare.

[I] Technically the WebSocket is a plain byte pipe that an automated client could drive. It is designed for browsers, is not documented for scripts, and may run into Cloudflare bot protection. Prefer SSH. Keep hterm as a fallback if our runtime can only reach HTTPS, and ask the admins first if we plan to use it programmatically.

---

## 9. Open questions to settle on the first live login

1. The exact text of lobby submenu `1` ("NetHack (various versions)"), and confirmation that `V` is 3.6.7 [U].
2. What `j) Manage settings` offers: rc edit, editor choice (rnano or virus), rc sync [U].
3. Whether Hardfought's sshd accepts `SetEnv DGLAUTH` [U].
4. The maximum username length (≥16 observed) [U].
5. The Hardfought logged-out banner text and the `s) Server information` text. The second might contain rules [U].
6. Admin stance on an AI/LLM account. Ask K2 or Tangles before playing [I].

---

## Sources

**Hardfought**
- https://www.hardfought.org/ (home: the us.hardfought.org notice, the registration line)
- https://www.hardfought.org/nethack/ (connection, fingerprints, rc editors, crash recovery, password reset, Beholder commands)
- https://www.hardfought.org/nethack/hterm/, https://www.hardfought.org/hterm/, https://www.hardfought.org/hterm/wstty.js
- https://www.hardfought.org/nethack/rcedit/, https://www.hardfought.org/nh/nethack/rcedit.php
- https://www.hardfought.org/nethack/dumplogs/, https://www.hardfought.org/nethack/ttyrecs/, https://www.hardfought.org/nethack/userdata/, https://www.hardfought.org/nethack/xlogfiles/
- https://www.hardfought.org/nethack/tournaments/, https://www.hardfought.org/nethack/irclogs/ (#hardfought logs via `https://www.hardfought.org/nh/browseirc_hdf_db.php`: days 2026-09-07 to 09-25 plus the global-search hits on 2026-02-16, 05-03, 06-11, 09-21, 09-23 and 09-24)
- https://www.hardfought.org/updates-to-dgl-and-hterm/ (2020), https://www.hardfought.org/ssh-nethackhardfought-org/ (2017)
- https://www.hardfought.org/xlogfiles/nethack36/xlogfile, `…/nethack36/livelog`, `…/nethack50/xlogfile`, `…/nethack37/xlogfile`; https://eu.hardfought.org/xlogfiles/nethack36/xlogfile; https://au.hardfought.org/xlogfiles/nethack36/xlogfile
- https://www.hardfought.org/userdata/C/CodexDelver/ (including `lastgame`, `nethack/CodexDelver.nh36rc` and `nethack/dumplog/1788964024.nh.txt`)
- https://www.hardfought.org/nh/nethack/browsettyrec-us.php?player=CodexDelver, https://www.hardfought.org/nh/nethack/browsedumplog-us.php?player=CodexDelver, https://www.hardfought.org/nh/index.php

**Hardfought server source**
- https://github.com/k21971/NetHack36 (branch `hardfought`): `sys/unix/hints/hardfought`, `sys/unix/sysconf`, `include/config.h`, `include/unixconf.h`, `src/options.c`, `src/mail.c`, `win/tty/topl.c`, `win/curses/cursmesg.c`, `win/curses/cursmain.c`, `sys/unix/unixunix.c`, `install-to-chroot.sh`
- https://github.com/k21971/dgamelaunch: `README`, `Changelog`, `dgamelaunch.c`, `dgl-common.c`, `ttyrec.c`, `examples/*`, `dgl-default-rcfile`

**NAO**
- https://www.alt.org/nethack/ (home), https://www.alt.org/nethack/news.php, https://www.alt.org/nethack/ssh_fingerprints.txt, https://www.alt.org/nethack/hterm/ (with `wstty.js`), https://www.alt.org/nethack/webconf/, https://www.alt.org/nethack/naonh.php
- https://www.alt.org/nethack/mostrecent.php (the embedded data and `explore.js`), https://www.alt.org/nethack/userdata/p/pakka/, https://www.alt.org/nethack/xlogfile.nh500, https://www.alt.org/nethack/xlogfile.nh363+, https://archive.alt.org/archive/index.html
- https://github.com/altorg/nao-server (`README-ssh`, `os/sshd.txt`, `os/xinetd.d/dgl`), https://github.com/altorg/dgamelaunch (`dgamelaunch.c`, `examples/*`)

**Versions**
- https://www.nethack.org/, https://www.nethack.org/common/news.html, https://www.nethack.org/v500/release.html
- NetHack Wiki: https://nethackwiki.com/wiki/NetHack_3.7.0, https://nethackwiki.com/wiki/Nethack.alt.org, https://nethackwiki.com/wiki/Hardfought, https://nethackwiki.com/wiki/Public_server, https://nethackwiki.com/wiki/Dgamelaunch, https://nethackwiki.com/wiki/Hangup, https://nethackwiki.com/wiki/Bot

**Policies and tournaments**
- https://tnnt.org/faq, https://junethack.net/rules, https://junethack.net/
- https://github.com/krajj7/BotHack (`README.md`, `doc/running.md`)

**Scoreboard**
- https://nethackscoreboard.org/about.html, https://nethackscoreboard.org/ascended.nh.html, https://nethackscoreboard.org/players/C/CodexDelver.nh.html

**Astra (another team's harness, read-only)**
- Local copy at `/home/user/kenforthewin/nethack_astra`: `scripts/session.py`, `docs/SETUP.md`, `docs/METHODOLOGY.md`, `docs/RECORDINGS.md`, `config/nethackrc`, `config/known_hosts`, `config/tmux.conf`, `memory/session.md`, `memory/live-run.md`, `memory/run-3.md`, `EVIDENCE.md`
- The public evidence archive https://github.com/kenforthewin/nethack_astra/releases/tag/v1.0.0 (`nethack-evidence.tar.gz`, SHA256 `73e7b58070fe0b8906494f4b02ec65513d82ec486eb00f648cd9ee0f3e85b1c9`, verified). From it I used `events.jsonl.gz` (lobby screens, `Pane is dead (status N)` snapshots, input and output timings) and the ttyrecs `2026-09-06.18:44:41.260`, `2026-09-08.17:42:42.254`, `2026-09-20.15:10:10.120` and `2026-09-20.15:54:29.653`.
- https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/

**DNS**
- Cloudflare DNS-over-HTTPS lookups (`https://cloudflare-dns.com/dns-query`) for the server hostnames, 2026-09-26.
