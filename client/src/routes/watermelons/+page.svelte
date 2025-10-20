<script lang="ts">
	type Ratings = {
		texture: number;
		juiciness: number;
		sweetness: number;
	};

	type Watermelon = {
		id: number;
		src: string;
		createdAt: Date;
		rachy: Ratings;
		davey: Ratings;
	};

	let watermelons: Watermelon[] = [];
	let nextId = 0;

	function handleFileUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files[0]) {
			const file = target.files[0];
			const reader = new FileReader();
			reader.onload = (e) => {
				if (typeof e.target?.result === 'string') {
					const newWatermelon: Watermelon = {
						id: nextId++,
						src: e.target.result,
						createdAt: new Date(),
						rachy: {
							texture: 50,
							juiciness: 50,
							sweetness: 50
						},
						davey: {
							texture: 50,
							juiciness: 50,
							sweetness: 50
						}
					};
					watermelons = [...watermelons, newWatermelon];
				}
			};
			reader.readAsDataURL(file);
		}
	}
</script>

<div class="p-8 min-h-full">
	<h1 class="text-5xl text-rose-500 font-bold mb-10 text-center">Our Watermelon Memories</h1>

	<div class="mb-12 text-center">
		<label
			for="file-upload"
			class="cursor-pointer bg-rose-400 hover:bg-rose-500 text-white font-bold py-3 px-6 rounded-full shadow-lg transition-transform transform hover:scale-105"
		>
			+ Add a Watermelon Memory
		</label>
		<input
			id="file-upload"
			type="file"
			class="hidden"
			on:change={handleFileUpload}
			accept="image/*"
		/>
	</div>

	{#if watermelons.length === 0}
		<div class="text-center py-20">
			<p class="text-gray-500 text-lg">Upload a photo to start tracking your watermelon memories!</p>
			<div class="text-6xl mt-4">🍉</div>
		</div>
	{/if}

	<div class="space-y-12 p-4">
		{#each watermelons as watermelon (watermelon.id)}
			<div class="bg-white p-6 shadow-md rounded-lg w-full border border-rose-100">
				<div class="flex flex-col lg:flex-row gap-8 items-start">
					<div class="w-full lg:w-1/3">
						<img
							src={watermelon.src}
							alt="A watermelon"
							class="w-full h-80 object-cover rounded-md border-2 border-rose-100"
						/>
						<p class="text-center text-gray-500 mt-2">
							{watermelon.createdAt.toLocaleDateString('en-US', {
								year: 'numeric',
								month: 'long',
								day: 'numeric'
							})}
						</p>
					</div>
					<div class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-8 w-full">
						<div>
							<h3 class="text-2xl font-bold text-pink-400 mb-4 text-center">Rachy's Rating</h3>
							<div class="mb-4">
								<label
									for="rachy-texture-{watermelon.id}"
									class="block text-lg font-medium text-gray-700">Texture</label
								>
								<input
									type="range"
									id="rachy-texture-{watermelon.id}"
									bind:value={watermelon.rachy.texture}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<div class="mb-4">
								<label
									for="rachy-juiciness-{watermelon.id}"
									class="block text-lg font-medium text-gray-700">Juiciness</label
								>
								<input
									type="range"
									id="rachy-juiciness-{watermelon.id}"
									bind:value={watermelon.rachy.juiciness}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<div>
								<label
									for="rachy-sweetness-{watermelon.id}"
									class="block text-lg font-medium text-gray-700">Sweetness</label
								>
								<input
									type="range"
									id="rachy-sweetness-{watermelon.id}"
									bind:value={watermelon.rachy.sweetness}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<div class="mt-6 text-center">
								<div class="text-7xl font-bold text-pink-400">
									{Math.round(
										(watermelon.rachy.texture +
											watermelon.rachy.juiciness +
											watermelon.rachy.sweetness) /
											3
									)}
								</div>
							</div>
						</div>
						<div>
							<h3 class="text-2xl font-bold text-sky-400 mb-4 text-center">Davey's Rating</h3>
							<div class="mb-4">
								<label
									for="davey-texture-{watermelon.id}"
									class="block text-lg font-medium text-gray-700">Texture</label
								>
								<input
									type="range"
									id="davey-texture-{watermelon.id}"
									bind:value={watermelon.davey.texture}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<div class="mb-4">
								<label
									for="davey-juiciness-{watermelon.id}"
									class="block text-lg font-medium text-gray-700">Juiciness</label
								>
								<input
									type="range"
									id="davey-juiciness-{watermelon.id}"
									bind:value={watermelon.davey.juiciness}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<div>
								<label
									for="davey-sweetness-{watermelon.id}"
									class="block text-lg font-medium text-gray-700">Sweetness</label
								>
								<input
									type="range"
									id="davey-sweetness-{watermelon.id}"
									bind:value={watermelon.davey.sweetness}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<div class="mt-6 text-center">
								<div class="text-7xl font-bold text-sky-400">
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
				</div>
			</div>
		{/each}
	</div>
</div>
