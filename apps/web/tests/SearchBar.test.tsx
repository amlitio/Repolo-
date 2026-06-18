import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SearchBar } from "@/components/map/SearchBar";
import * as endpoints from "@/lib/api/endpoints";
import type { MapSearchResult } from "@/lib/api/endpoints";

const RESULTS: MapSearchResult[] = [
  { type: "county", id: "12103", name: "Pinellas County", fips: "12103", centroid: [-82.7, 27.9] },
];

function renderWithQueryClient(children: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>);
}

describe("SearchBar", () => {
  beforeEach(() => {
    vi.spyOn(endpoints, "searchMap").mockResolvedValue(RESULTS);
  });

  it("does not query until at least 2 characters are typed", async () => {
    const searchSpy = vi.spyOn(endpoints, "searchMap");
    const user = userEvent.setup();
    renderWithQueryClient(<SearchBar onSelectResult={vi.fn()} />);

    const input = screen.getByPlaceholderText(/search county, city, or property/i);
    await user.type(input, "P");

    expect(searchSpy).not.toHaveBeenCalled();
  });

  it("queries and renders results once 2+ characters are typed", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<SearchBar onSelectResult={vi.fn()} />);

    const input = screen.getByPlaceholderText(/search county, city, or property/i);
    await user.type(input, "Pinellas");

    expect(await screen.findByText("Pinellas County")).toBeInTheDocument();
  });

  it("calls onSelectResult with the chosen result when clicked", async () => {
    const onSelectResult = vi.fn();
    const user = userEvent.setup();
    renderWithQueryClient(<SearchBar onSelectResult={onSelectResult} />);

    const input = screen.getByPlaceholderText(/search county, city, or property/i);
    await user.type(input, "Pinellas");

    const resultButton = await screen.findByText("Pinellas County");
    await user.click(resultButton);

    expect(onSelectResult).toHaveBeenCalledWith(RESULTS[0]);
  });

  it("shows a 'no matches' message when the query returns an empty array", async () => {
    vi.spyOn(endpoints, "searchMap").mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQueryClient(<SearchBar onSelectResult={vi.fn()} />);

    const input = screen.getByPlaceholderText(/search county, city, or property/i);
    await user.type(input, "Nowhere");

    expect(await screen.findByText(/no matches for/i)).toBeInTheDocument();
  });

  it("switches to the Ask tab and submits a research question", async () => {
    const askSpy = vi.spyOn(endpoints, "askResearch").mockResolvedValue({
      answer: "Pinellas County risk is driven primarily by storm surge exposure.",
      citations: [],
    });
    const user = userEvent.setup();
    renderWithQueryClient(<SearchBar onSelectResult={vi.fn()} />);

    await user.click(screen.getByRole("tab", { name: /ask/i }));
    const askInput = screen.getByPlaceholderText(/ask about flood risk/i);
    await user.type(askInput, "What drives risk in Pinellas?");
    await user.click(screen.getByRole("button", { name: /ask/i }));

    await waitFor(() => expect(askSpy).toHaveBeenCalledWith({ question: "What drives risk in Pinellas?" }));
    expect(await screen.findByText(/storm surge exposure/i)).toBeInTheDocument();
  });
});
