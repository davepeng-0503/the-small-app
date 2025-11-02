// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}

		type Ratings = {
			texture: number;
			juiciness: number;
			sweetness: number;
		};

		type Watermelon = {
			id: string;
			src: string;
			createdAt: Date;
			rachy: Ratings;
			davey: Ratings;
		};

		type Sticker = {
			id: string;
			src: string;
			x: number;
			y: number;
			rotation: number;
			scale: number;
			on_back: boolean;
		};

		type Polaroid = {
			id: string;
			src: string;
			createdAt: Date;
			description: string;
			diaryEntry: string;
			stickers: Sticker[];
		};

		type TimelineItem = (Watermelon & { type: 'watermelon' }) | (Polaroid & { type: 'polaroid' });
	}
}

export {};
