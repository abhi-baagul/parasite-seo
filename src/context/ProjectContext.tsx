"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { ApiClientError } from "@/services/api-client";
import { listProjects } from "@/services/project-service";
import type { ProjectDto } from "@/services/types";

interface ProjectContextValue {
  projects: ProjectDto[];
  selectedId: string;
  selectedProject: ProjectDto | undefined;
  setSelectedId: (id: string) => void;
  loading: boolean;
  error: string | null;
  refreshProjects: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextValue | null>(null);

export function ProjectProvider({ children }: { children: React.ReactNode }) {
  const [projects, setProjects] = useState<ProjectDto[]>([]);
  const [selectedId, setSelectedId] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listProjects();
      setProjects(result.items);
      setSelectedId((current) => {
        if (current === "all") return current;
        return result.items.some((item) => item.id === current) ? current : "all";
      });
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : "Unable to load projects";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useAsyncLoad(() => refreshProjects(), [refreshProjects]);

  const value = useMemo(
    () => ({
      projects,
      selectedId,
      selectedProject: projects.find((project) => project.id === selectedId),
      setSelectedId,
      loading,
      error,
      refreshProjects,
    }),
    [projects, selectedId, loading, error, refreshProjects],
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProject must be used within ProjectProvider");
  return ctx;
}
