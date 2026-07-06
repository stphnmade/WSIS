import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

const PLACE = {
  place_geoid: "0668000", slug: "san-jose-ca", name: "San Jose", state_code: "CA",
  latitude: 37.33, longitude: -121.89, active_listing_count: 92,
  latest_listing_date: "2026-07-05", coverage_status: "job_feed_covered",
};

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    const payload = url.includes("/api/v1/explore") ? [PLACE] : [];
    return { ok: true, json: async () => payload } as Response;
  }));
});

afterEach(() => vi.unstubAllGlobals());

describe("WSIS responsive product flow", () => {
  it("starts as a guest without assuming a user intent", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Find places where your work and life can fit." })).toBeVisible();
    expect(screen.getByRole("button", { name: "Explore without a plan" })).toBeVisible();
    expect(screen.getByText("Explore first. Sign in only when you want to save.")).toBeVisible();
    await waitFor(() => expect(fetch).toHaveBeenCalled());
  });

  it("moves through questions into five-place results", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Find places with work for me" }));

    expect(screen.getByRole("heading", { name: "Give us the useful constraints." })).toBeVisible();
    fireEvent.change(screen.getByRole("textbox", { name: "Desired role or skill" }), { target: { value: "Data analyst" } });
    fireEvent.click(screen.getByRole("button", { name: /Show my five places/ }));

    expect(await screen.findByRole("heading", { name: "Places where work and life can fit." })).toBeVisible();
    expect(screen.getByRole("heading", { name: "San Jose" })).toBeVisible();
  });

  it("allows anonymous exploration without onboarding", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Explore without a plan" }));

    expect(await screen.findByRole("heading", { name: "Explore beyond your first five." })).toBeVisible();
    expect(screen.getAllByRole("button", { name: /San Jose, CA/ })).toHaveLength(2);
  });
});
