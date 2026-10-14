import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(
  new URL("../src/page/home/index.vue", import.meta.url),
  "utf8",
);
const script = source.match(/<script>([\s\S]*?)<\/script>/)[1];

function home(getDevices) {
  const timers = [];
  const context = vm.createContext({
    SourceDialog: {},
    api: { getDevices },
    clearTimeout: (timer) => {
      timer.cancelled = true;
    },
    console: { error() {} },
    setTimeout: (callback, delay) => {
      const timer = { callback, delay };
      timers.push(timer);
      return timer;
    },
  });
  vm.runInContext(
    script
      .replace(/^import .*;\s*$/gm, "")
      .replace("export default", "globalThis.component ="),
    context,
  );
  const component = context.component;
  const state = component.data();
  for (const [name, method] of Object.entries(component.methods)) {
    state[name] = method.bind(state);
  }
  return { component, state, timers };
}

test("devices refresh after an initially empty discovery result", async () => {
  const results = [[], [{ name: "Living Room", status: "paired" }]];
  const { state, timers } = home(() =>
    Promise.resolve({ data: results.shift() }),
  );
  await state.refreshDevices();
  assert.equal(state.devices.length, 0);
  assert.equal(timers[0].delay, 5000);
  await timers[0].callback();
  assert.equal(state.devices[0].name, "Living Room");
  assert.equal(timers.length, 2);
});

test("a temporary API failure retains devices and schedules another refresh", async () => {
  const { state, timers } = home(() => Promise.reject(new Error("offline")));
  state.devices = [{ name: "Spare Room" }];
  await state.refreshDevices();
  assert.equal(state.devices[0].name, "Spare Room");
  assert.equal(timers.length, 1);
});

test("leaving home stops polling even when a request is still pending", async () => {
  let resolve;
  const { component, state, timers } = home(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  const pending = state.refreshDevices();
  state.deviceRefreshTimer = {};
  component.unmounted.call(state);
  resolve({ data: [{ name: "Late Result" }] });
  await pending;
  assert.equal(state.devices.length, 0);
  assert.equal(timers.length, 0);
  assert.equal(state.deviceRefreshTimer.cancelled, true);
});

test("a connected TV's pairing advertisement does not invite pairing again", () => {
  const { component, state } = home(() => Promise.resolve({ data: [] }));
  state.devices = [
    { ip: "10.0.0.100", status: "pairable" },
    { ip: "10.0.0.100", status: "paired" },
    { ip: "10.0.0.101", status: "pairable" },
  ];
  const pairable = component.computed.pairableDevices.call(state);
  assert.equal(pairable.length, 1);
  assert.equal(pairable[0].ip, "10.0.0.101");
});
