"use client";

import { useState } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { Spinner } from "@/components/ui/States";
import { useMapSearch } from "@/lib/hooks/useMapSearch";
import { useAskResearch } from "@/lib/hooks/useAskResearch";
import type { MapSearchResult } from "@/lib/api/endpoints";

export interface SearchBarProps {
  onSelectResult: (result: MapSearchResult) => void;
}

/** County/city/property search (GET /map/search) + natural-language research input (POST /research/ask). */
export function SearchBar({ onSelectResult }: SearchBarProps) {
  const [mode, setMode] = useState<"search" | "ask">("search");
  const [query, setQuery] = useState("");
  const [question, setQuestion] = useState("");

  const { data: results, isLoading, isError } = useMapSearch(query);
  const askResearch = useAskResearch();

  function handleAskSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    askResearch.mutate({ question: trimmed });
  }

  return (
    <div className="border-b border-slate-800 bg-slate-950 p-2">
      <Tabs value={mode} onValueChange={(value) => setMode(value as "search" | "ask")}>
        <TabsList>
          <TabsTrigger value="search">Search</TabsTrigger>
          <TabsTrigger value="ask">Ask</TabsTrigger>
        </TabsList>

        <TabsContent value="search">
          <div className="relative">
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search county, city, or property…"
              aria-label="Search county, city, or property"
            />
            {isLoading ? (
              <Spinner className="absolute right-2 top-1/2 -translate-y-1/2" />
            ) : null}
          </div>

          {isError ? (
            <p className="mt-1 text-[11px] text-red-400">Search failed. Try again.</p>
          ) : null}

          {results && results.length > 0 ? (
            <ul className="mt-1 max-h-64 overflow-y-auto rounded-sm border border-slate-800 bg-slate-900">
              {results.map((result) => (
                <li key={`${result.type}-${result.id}`}>
                  <button
                    type="button"
                    onClick={() => onSelectResult(result)}
                    className="flex w-full items-center justify-between px-2 py-1.5 text-left text-xs text-slate-200 hover:bg-slate-800"
                  >
                    <span className="truncate">{result.name}</span>
                    <span className="font-mono text-[10px] uppercase text-slate-500">
                      {result.type}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}

          {query.trim().length > 1 && !isLoading && !isError && results?.length === 0 ? (
            <p className="mt-1 text-[11px] text-slate-500">No matches for &quot;{query}&quot;.</p>
          ) : null}
        </TabsContent>

        <TabsContent value="ask">
          <form onSubmit={handleAskSubmit} className="flex gap-2">
            <Input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask about flood risk, e.g. “What drives risk in Pinellas County?”"
              aria-label="Ask a research question"
            />
            <Button type="submit" size="sm" disabled={askResearch.isPending}>
              {askResearch.isPending ? <Spinner /> : "Ask"}
            </Button>
          </form>

          {askResearch.isError ? (
            <p className="mt-1 text-[11px] text-red-400">
              {askResearch.error instanceof Error ? askResearch.error.message : "Request failed."}
            </p>
          ) : null}

          {askResearch.data ? (
            <div className="mt-2 space-y-2 rounded-sm border border-slate-800 bg-slate-900 p-2">
              <p className="text-xs leading-relaxed text-slate-200">{askResearch.data.answer}</p>
              {askResearch.data.citations.length > 0 ? (
                <ul className="space-y-1">
                  {askResearch.data.citations.map((citation, index) => (
                    <li key={`${citation.source_id}-${index}`} className="text-[10px] text-slate-500">
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-400 hover:underline"
                      >
                        {citation.source_id}
                      </a>
                      {" - "}
                      {citation.snippet}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </TabsContent>
      </Tabs>
    </div>
  );
}
