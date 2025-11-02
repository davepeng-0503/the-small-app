<script lang="ts">
	import { onMount } from 'svelte';

	const API_URL = 'http://localhost:9999';
	let timelineItems: App.TimelineItem[] = [];

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
			const polaroids: (App.Polaroid & { type: 'polaroid' })[] = polaroidsData.map((p: any) => {
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

			const watermelons: (App.Watermelon & { type: 'watermelon' })[] = watermelonsData.map(
				(w: any) => ({
					...w,
					type: 'watermelon',
					createdAt: new Date(w.createdAt)
				})
			);

			timelineItems = [...polaroids, ...watermelons].sort(
				(a, b) => b.createdAt.getTime() - a.createdAt.getTime()
			);
		} catch (error) {
			console.error('Error fetching timeline data:', error);
		}
	});

	function observe(node: HTMLElement, item: App.TimelineItem) {
		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						node.classList.add('visible');
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

	function triggerStickerFall(stickers: App.Sticker[]) {
		const newStickers = [];
		for (const sticker of stickers) {
			newStickers.push({
				id: Date.now() + stickers.indexOf(sticker),
				src: sticker.src,
				x: Math.random() * 100, // as vw percentage
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
		<h1 class="text-5xl text-rose-500 font-bold mb-12 text-center">Our Timeline</h1>

		{#if timelineItems.length === 0}
			<div class="text-center py-20 text-gray-500">Loading timeline...</div>
		{:else}
			<div class="relative max-w-4xl mx-auto">
				<!-- The timeline's central line -->
				<div
					class="absolute left-1/2 top-0 h-full w-1 bg-rose-200 transform -translate-x-1/2"
				></div>

				{#each timelineItems as item, i (item.id)}
					<div class="timeline-item mb-12" use:observe={item}>
						<div
							class="timeline-content-wrapper relative flex items-center"
							class:justify-start={i % 2 === 0}
							class:justify-end={i % 2 !== 0}
						>
							<div
								class="absolute left-1/2 w-12 h-12 bg-rose rounded-full z-10 transform -translate-x-1/2 border-4 border-rose-50"
							></div>

							<div
								class="timeline-content w-[calc(50%-2rem)] p-4 bg-white shadow-lg rounded-lg border border-rose-100"
								class:mr-auto={i % 2 === 0}
								class:ml-auto={i % 2 !== 0}
							>
								<div class="text-sm text-gray-500 mb-2">
									{item.createdAt.toLocaleDateString('en-US', {
										year: 'numeric',
										month: 'long',
										day: 'numeric'
									})}
								</div>

								{#if item.type === 'polaroid'}
									{@const polaroid = item}
									<div class="polaroid-card">
										<img
											src={polaroid.src}
											alt={polaroid.description}
											class="w-full h-auto object-cover rounded-sm mb-2"
										/>
										<p class="italic text-sm text-gray-700">{polaroid.description}</p>
									</div>
								{:else if item.type === 'watermelon'}
									{@const watermelon = item}
									<div class="watermelon-card">
										<img
											src={watermelon.src}
											alt="Watermelon"
											class="w-full h-auto object-cover rounded-md mb-2"
										/>
										<div class="flex justify-around text-center mt-2">
											<div>
												<div class="text-lg font-bold text-pink-400">Rachy</div>
												<div class="text-2xl font-bold text-pink-400">
													{Math.round(
														(watermelon.rachy.texture +
															watermelon.rachy.juiciness +
															watermelon.rachy.sweetness) /
															3
													)}
												</div>
											</div>
											<div>
												<div class="text-lg font-bold text-sky-400">Davey</div>
												<div class="text-2xl font-bold text-sky-400">
													{Math.round(
														(watermelon.davey.texture +
															watermelon.davey.juiciness +
															watermelon.davey.sweetness) /
															3
													)}
												</div>
											</div>
										</div>
									</div>
								{/if}
							</div>
						</div>
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
