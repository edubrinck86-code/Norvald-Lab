import { createContext, useContext } from "react";
import type { ResourceReference } from "./resourceReference";
export const ResourceReferenceContext = createContext<{ open(reference: ResourceReference): void } | null>(null);
export function useResourceReferences() { return useContext(ResourceReferenceContext); }
