import { writable } from "svelte/store";
import type { Polaroid, Watermelon } from "../app";

export const photos = writable<((Polaroid | Watermelon) & {
  x: number;
  y: number;
  rotation: number;
})[]>([])