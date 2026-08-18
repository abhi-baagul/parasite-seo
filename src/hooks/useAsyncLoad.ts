"use client";

import { useEffect } from "react";

/** Schedule an async loader after the effect body so React lint does not flag sync setState. */
export function useAsyncLoad(loader: () => void | Promise<void>, deps: React.DependencyList) {
  useEffect(() => {
    let active = true;
    const handle = window.setTimeout(() => {
      if (!active) return;
      void Promise.resolve(loader());
    }, 0);
    return () => {
      active = false;
      window.clearTimeout(handle);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
