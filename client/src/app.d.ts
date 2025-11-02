
export type Ratings = {
	texture: number;
	juiciness: number;
	sweetness: number;
};

export type Watermelon = {
	id: string;
	src: string;
	createdAt: Date;
	rachy: Ratings;
	davey: Ratings;
};

export type Sticker = {
	id: string;
	src: string;
	x: number;
	y: number;
	rotation: number;
	scale: number;
	on_back: boolean;
};

export type Polaroid = {
	id: string;
	src: string;
	createdAt: Date;
	description: string;
	diaryEntry: string;
	stickers: Sticker[];
};

export type TimelineItem = (Watermelon & { type: 'watermelon' }) | (Polaroid & { type: 'polaroid' });


export {};
