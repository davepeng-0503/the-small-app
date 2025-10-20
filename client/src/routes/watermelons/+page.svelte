<script lang="ts">
	type Watermelon = {
		id: number;
		src: string;
		sweetness: number;
		juiciness: number;
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
						sweetness: 5,
						juiciness: 5
					};
					watermelons = [...watermelons, newWatermelon];
				}
			};
			reader.readAsDataURL(file);
		}
	}
</script>

<div class="p-8 bg-yellow-50 min-h-full font-serif" style="background-image: url('data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%239C92AC" fill-opacity="0.1"%3E%3Cpath d="M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E');">
	<h1
		class="text-5xl text-green-700 font-bold mb-10 text-center"
		style="font-family: 'Comic Sans MS', cursive, sans-serif;"
	>
		Watermelon Scrapbook
	</h1>

	<div class="mb-12 text-center">
		<label
			for="file-upload"
			class="cursor-pointer bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-full shadow-lg transition-transform transform hover:scale-105"
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
		<p class="text-center text-gray-500">Upload a photo to start your scrapbook!</p>
	{/if}

	<div class="flex flex-wrap justify-center gap-10 p-4">
		{#each watermelons as watermelon (watermelon.id)}
			<div
				class="bg-white p-4 pb-6 shadow-xl rounded-lg transform -rotate-2 hover:rotate-1 hover:scale-105 transition-transform duration-300 ease-in-out w-72"
			>
				<img
					src={watermelon.src}
					alt="A watermelon"
					class="w-full h-64 object-cover rounded-md mb-4 border-2 border-gray-100"
				/>
				<div class="px-2">
					<div class="mb-3">
						<label for="sweetness-{watermelon.id}" class="block text-sm font-medium text-gray-700"
							>Sweetness</label
						>
						<input
							type="range"
							id="sweetness-{watermelon.id}"
							bind:value={watermelon.sweetness}
							min="1"
							max="10"
							class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
						/>
					</div>
					<div>
						<label for="juiciness-{watermelon.id}" class="block text-sm font-medium text-gray-700"
							>Juiciness</label
						>
						<input
							type="range"
							id="juiciness-{watermelon.id}"
							bind:value={watermelon.juiciness}
							min="1"
							max="10"
							class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
						/>
					</div>
				</div>
			</div>
		{/each}
	</div>
</div>
