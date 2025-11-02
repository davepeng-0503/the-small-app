<script lang="ts">
	import { onMount } from 'svelte';
  import type { Polaroid, Sticker, TimelineItem, Watermelon } from '../../app';
  import TimelineImage from '$lib/components/TimelineImage.svelte';
  import TimelineDisplay from '$lib/components/TimelineDisplay.svelte';

	const API_URL = 'http://localhost:9999';
	let timelineItems: (TimelineItem & { left: boolean })[] = [];

	// --- Sticker Fall ---
	let allStickers: string[] = [];
	let fallingStickers: {
		id: number;
		src: string;
		x: number;
		duration: number;
		delay: number;
		scale: number;
		rotation: number;
	}[] = [];

	onMount(async () => {
		try {
			const [polaroidsRes, watermelonsRes] = await Promise.all([
				fetch(`${API_URL}/polaroids`),
				fetch(`${API_URL}/watermelons`)
			]);

			if (!polaroidsRes.ok || !watermelonsRes.ok) {
				throw new Error('Failed to fetch timeline data');
			}

			const polaroidsData = await polaroidsRes.json();
			const watermelonsData = await watermelonsRes.json();

			const uniqueStickerUrls = new Set<string>();
			const polaroids: (Polaroid & { type: 'polaroid' })[] = polaroidsData.map((p: any) => {
				p.stickers?.forEach((s: any) => uniqueStickerUrls.add(s.src));
				return {
					...p,
					type: 'polaroid',
					createdAt: new Date(p.createdAt),
					diaryEntry: p.diary_entry || '',
					stickers: p.stickers?.map((s: any) => ({ ...s, src: s.src })) || []
				};
			});

			allStickers = Array.from(uniqueStickerUrls);

			const watermelons: (Watermelon & { type: 'watermelon' })[] = watermelonsData.map(
				(w: any) => ({
					...w,
					type: 'watermelon',
					createdAt: new Date(w.createdAt)
				})
			);

			timelineItems = [...polaroids, ...watermelons].sort(
				(a, b) => b.createdAt.getTime() - a.createdAt.getTime()
			).map((ti) => {
				return {
					...ti,
					left: ti.createdAt.getTime() % 2 === 1
				}
			});
		} catch (error) {
			console.error('Error fetching timeline data:', error);
		}
	});

	function observe(node: HTMLElement, item: TimelineItem) {
		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						if (item.type === 'polaroid' && allStickers.length > 0) {
							triggerStickerFall(item.stickers);
						}
					}
				});
			},
			{ threshold: 0.1 }
		);

		observer.observe(node);

		return {
			destroy() {
				observer.unobserve(node);
			}
		};
	}

	function triggerStickerFall(stickers: Sticker[]) {
		const newStickers = [];
		for (const sticker of stickers) {
			newStickers.push({
				id: Date.now() + stickers.indexOf(sticker),
				src: sticker.src,
				x:  Math.random() * 100 - 34, // as vw percentage
				duration: Math.random() * 2 + 3, // 3s to 5s
				delay: Math.random() * 2, // 0s to 2s
				scale: Math.random() * 0.1 + 0.075, // 20% to 60%
				rotation: Math.random() * 360
			});
		}
		fallingStickers = [...fallingStickers, ...newStickers];
	}

	function removeSticker(id: number) {
		fallingStickers = fallingStickers.filter((s) => s.id !== id);
	}
</script>

<svelte:head>
	<title>Our Timeline</title>
</svelte:head>

<div class="relative overflow-x-hidden bg-rose-50">
	<div class="sticker-fall-container fixed top-0 left-0 w-full h-full pointer-events-none z-50">
		{#each fallingStickers as sticker (sticker.id)}
			<img
				src={sticker.src}
				alt="falling sticker"
				class="absolute animate-fall"
				style="
          --scale: {sticker.scale};
          --initial-rotation: {sticker.rotation}deg;
					top: -2000px;
          left: {sticker.x}vw;
          animation-duration: {sticker.duration}s;
          animation-delay: {sticker.delay}s;
          transform: rotate(var(--initial-rotation)) scale(var(--scale));
        "
				on:animationend={() => removeSticker(sticker.id)}
			/>
		{/each}
	</div>

	<div class="p-6 min-h-full w-full">
		<h1 class="text-5xl text-rose-500 font-bold mb-12 text-center h-full">Our Timeline</h1>

		{#if timelineItems.length === 0}
			<div class="text-center py-20 text-gray-500">Loading timeline...</div>
		{:else}
			<div class="relative max-w-4xl mx-auto h-full">
				<!-- The timeline's central line -->
				<div
					class="absolute left-1/2 top-0 h-full w-1 bg-rose-200 transform -translate-x-1/2"
				>
				</div>

				{#each timelineItems as item, i (item.id)}
					<div class="mb-12 grid grid-cols-3" use:observe={item}>
						{#if item.left}
						<TimelineImage
							{item}
						/>
						{:else}
						<TimelineDisplay
							{item}
						/>
						{/if}
						<div class="ml-auto mr-auto z-50 text-7xl text-rose-700	">
							<div class="-mt-[42px] transform translate-y-1/2 h-full pt-0">
								•
							</div>
						</div>
						{#if item.left}
						<TimelineDisplay
							{item}
						/>
						{:else}
						<TimelineImage
							{item}
						/>
						{/if}
					</div>
				{/each}

			</div>
		{/if}
	</div>
</div>

<style>
	.timeline-item {
		opacity: 0;
		transform: translateY(50px);
		transition:
			opacity 0.6s ease-out,
			transform 0.6s ease-out;
	}
	.timeline-item.visible {
		opacity: 1;
		transform: translateY(0);
	}

	@keyframes fall {
		from {
			top: -100vh;
			transform: rotate(var(--initial-rotation)) scale(var(--scale));
			opacity: 1;
		}
		to {
			top: 110vh;
			transform: rotate(calc(var(--initial-rotation) + 720deg)) scale(var(--scale));
			opacity: 0.5;
		}
	}
	.animate-fall {
		animation-name: fall;
		animation-timing-function: linear;
		animation-fill-mode: forwards;
	}
</style>
