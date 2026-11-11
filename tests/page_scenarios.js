/* Scenarios run inside the control-center page, against the stubbed runtime (tests/stub/claude_stub.js).
   tools/render_page.py prepends `const SCENARIO = "<name>";`. The result is JSON in #__result. */
(function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const $$ = (s, root) => [...(root || document).querySelectorAll(s)];
  const btn = (text, root) => $$("button", root).find((b) => b.textContent.trim() === text);
  const flush = async () => { await sleep(60); renderApp(); await sleep(20); };   // headless virtual time may not run requestAnimationFrame
  const click = async (el) => { if (!el) throw new Error("missing element"); el.click(); await flush(); };
  const type = async (el, v) => { if (!el) throw new Error("missing input"); el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); await sleep(30); };
  const tab = async (n) => click(document.getElementById("tab-" + n));
  const writes = () => window.__SSK_WRITES;
  const last = (path) => [...writes()].reverse().find((w) => w.path === path);
  const text = () => document.getElementById("app").textContent;

  const S = {
    async boot() {
      return { tabs: $$("[role=tab]").map((t) => t.textContent.trim()), brand: document.querySelector("h1").textContent, readonly: /look but not change|Aquí solo puedes mirar|chỉ xem được/.test(text()) };
    },
    async approvals() {
      await tab("approvals");
      const cards = $$("article.appr");
      const first = cards[2];                                 // an unmarked item
      await click(btn("Approve", first));
      const ids = writes().filter((w) => w.path.startsWith("approvals/")).map((w) => w.op + " " + w.path);
      await click(btn("Approve", $$("article.appr")[2]));      // second click clears the mark
      const afterToggle = writes().filter((w) => w.path.startsWith("approvals/")).map((w) => w.op);
      await click(btn("Edit", $$("article.appr")[3]));
      const note = $$("article.appr")[3].querySelector("input[type=text]");
      await type(note, "Say it shorter");
      await flush();
      const editWrite = [...writes()].reverse().find((w) => w.path.startsWith("approvals/") && w.data && w.data.decision === "edit" && w.data.note === "Say it shorter");
      return { cards: cards.length, ids, afterToggle, editWrite: editWrite && editWrite.data, summaryText: document.querySelector(".summary-bar").textContent, phrase: /approved as marked|aprobado como marqué|đã duyệt như đã đánh dấu/.test(text()) };
    },
    async setup_brand() {
      const input = $$("input[type=text]").find((i) => i.value === "Demo Co");
      await type(input, "Acme Seeds");
      const flagVisible = !document.getElementById("dirtyflag").hidden;
      await click(btn("Save"));
      const w = last("config/brand");
      return { flagVisible, write: w && w.data };
    },
    async setup_invalid() {
      const tz = $$("input[type=text]").find((i) => i.value === "Europe/Madrid");
      await type(tz, "Mars/Olympus");
      await click(btn("Save"));
      return { errors: $$(".errors li").map((l) => l.textContent), wrote: writes().length };
    },
    async channels_add() {
      await tab("channels");
      const ta = document.getElementById("pasteurls");
      await type(ta, "https://www.facebook.com/groups/555\nhttps://www.facebook.com/mypage\nnot a url\nhttps://www.facebook.com/groups/555");
      await click(btn("+ Add channels"));
      const rows = $$("table.tbl tbody tr").length;
      await click(btn("Save"));
      const w = last("config/channels");
      return { rows, channels: w && w.data.channels.map((c) => [c.id, c.kind, c.state, c.language, c.fit.join(",")]) };
    },
    async channels_activate_needs_date() {
      await tab("channels");
      const row = $$("table.tbl tbody tr")[2];
      const sel = $$("select", row).find((s) => [...s.options].some((o) => o.value === "active"));
      await type(sel, "active");
      await click(btn("Save"));
      return { errors: $$(".errors li").map((l) => l.textContent), wrote: !!last("config/channels") };
    },
    async categories_add() {
      const stepBtn = $$("button.step").find((b) => b.textContent.includes("Categories"));
      await click(stepBtn);
      await click(btn("+ Add category"));
      const rows = $$(".list-row");
      const label = $$("input[type=text]", rows[rows.length - 1])[0];
      await type(label, "Garden Tools");
      await click(btn("Save"));
      return { catalog: last("config/catalog") && last("config/catalog").data.categories.map((c) => c.id), funnel: last("config/funnel") && Object.keys(last("config/funnel").data.destinations), channels: !!last("config/channels") };
    },
    async facts_add() {
      await click($$("button.step").find((b) => b.textContent.includes("Facts")));
      await click(btn("+ Add fact"));
      const inputs = $$(".list-row input[type=text]");
      await type(inputs[inputs.length - 1], "We ship by the pallet.");
      await click($$(".list-row input[type=checkbox]")[0]);
      await click(btn("Save"));
      return { write: last("config/facts") && last("config/facts").data.facts };
    },
    async control() {
      await tab("control");
      await click(btn("Pause everything"));
      const paused = last("control/state").data;
      const banner = !!document.querySelector(".banner.paused");
      await click(btn("Daily run"));
      const req = writes().find((w) => w.path.startsWith("runRequests/") && w.data.kind === "daily-run" && w.data.status === "pending");
      const box = document.getElementById("notebox");
      await type(box, "Please post the offer in B1 now");
      await click(btn("Send note"));
      const note = writes().find((w) => w.path.startsWith("notes/"));
      const cb = $$("input[type=checkbox]").find((c) => c.closest("label") && /A1/.test(c.closest("label").textContent));
      cb.checked = true; cb.dispatchEvent(new Event("change", { bubbles: true })); await flush();
      return { paused, banner, req: req && req.data, note: note && note.data, pausedChannels: last("control/state").data.pausedChannels };
    },
    async schedule_invalid() {
      await tab("control");
      const t1 = $$("input[type=time]")[0];
      await type(t1, "");
      await click(btn("Save"));
      return { errors: $$(".errors li").map((l) => l.textContent), wrote: !!last("config/caps") };
    },
    async readonly() {
      const out = { banner: /look but not change/.test(text()) };
      await tab("approvals");
      const b = btn("Approve", $$("article.appr")[0]);
      out.disabled = b.disabled; b.click(); await sleep(80);
      await tab("control");
      out.pauseDisabled = btn("Pause everything").disabled;
      out.writes = writes().length;
      return out;
    },
    async dashboard() {
      await tab("dashboard");
      const out = {};
      for (const name of ["Overview", "Conversations", "Leads", "Posts", "Runs and scans", "Health"]) {
        await click(btn(name));
        out[name] = { rows: $$("table.tbl tbody tr").length, text: text().length };
      }
      await click(btn("Leads"));
      out.leadContact = $$("table.tbl td .mono").map((n) => n.textContent);
      return out;
    },
    async xss() {
      // shared data is untrusted: markup in a field must show as text
      const dbx = await claude.use("db");
      await dbx.doc("queue/evil").set({ id: "evil", date: "2099-01-01", queue: "queue", n: 1, channel: "A1", type: "reply", text: "<img src=x onerror=window.__PWNED=1><b>bold</b>", meaning: "<script>window.__PWNED=1<\/script>", category: "home" });
      await tab("approvals");
      await new Promise((r) => { setTimeout(r, 400); });
      return { pwned: !!window.__PWNED, hasImg: !!document.querySelector(".fbcard img"), shown: /<b>bold<\/b>/.test(text()) };
    },
  };
  window.addEventListener("load", () => {
    setTimeout(async () => {
      const out = { scenario: SCENARIO };
      try { out.result = await S[SCENARIO](); } catch (e) { out.error = String(e && e.message || e); }
      out.errs = window.__ERRS; out.writes = window.__SSK_WRITES;
      const pre = document.createElement("pre"); pre.id = "__result"; pre.textContent = JSON.stringify(out);
      document.body.append(pre);
    }, 1200);
  });
})();
