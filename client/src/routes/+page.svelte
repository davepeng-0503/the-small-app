<script lang="ts">
	import { onMount } from 'svelte';
	import type { Polaroid, Watermelon } from '../app';
  import { photos } from '$lib/stores';

	const API_URL = 'http://localhost:9999';
  let actioned = false

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

			const watermelons: (Watermelon & { type: 'watermelon' })[] = watermelonsData.map(
				(w: any) => ({
					...w,
					type: 'watermelon',
					createdAt: new Date(w.createdAt)
				})
			);

			const allPhotos = [...polaroids, ...watermelons]

      const totalMults = Math.ceil(550 / allPhotos.length)
      let allPhotosMultiplied: typeof allPhotos[number][] = []
      for (let i = 0; i < totalMults; i++) {
        allPhotosMultiplied = [...allPhotosMultiplied, ...allPhotos]
      }
      if ($photos.length === 0) {
        photos.set(allPhotosMultiplied.map(p => {
          return {
            ...p,
            x: Math.random() * 150 - 50, // left: 0% to 75% to keep it mostly on screen
            y: Math.random() * 150 - 50, // top: 0% to 70%
            rotation: Math.random() * 50 - 25,
          }
        }))
      }
		} catch (error) {
			console.error('Error fetching timeline data:', error);
		}
	});
  
  $: console.log($photos)
</script>

<svelte:head>
	<title>Rachy & Davey</title>
</svelte:head>

<div class="relative w-screen h-screen overflow-hidden bg-rose-50 font-sans">
  <!-- svelte-ignore block_empty -->
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
  {#if !actioned}
    <h1
      class="absolute w-full h-full text-8xl font-bold text-rose-800 z-9999 select-none rounded-md"
      on:click={(e) => {
        actioned = true
      }}
    >
      <div class="translate-x-1/5 translate-y-2/5 w-full h-full">
        Rachy & Davey
      </div>
    </h1>
  {/if}

	<div class="absolute top-0 left-0 w-full h-full">
		{#each $photos as photo, i}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				class="polaroid-container select-none absolute z-0 bg-gray-100 p-2 shadow-xl transition-transform duration-300 hover:scale-110 hover:z-50 cursor-pointer"
				style="top: {photo.y}%; left: {photo.x}%; transform: rotate({photo.rotation}deg); z-index: {i +
					1};"
        on:mouseenter|stopPropagation|preventDefault={(e) => {
          if (e.shiftKey) {
            const el = e.currentTarget;
      
            const currentX = photo.x;
            const currentY = photo.y;
        
            const distToTop = currentY;
            const distToBottom = 100 - currentY;
            const distToLeft = currentX;
            const distToRight = 100 - currentX;
        
            const minDist = Math.min(distToTop, distToBottom, distToLeft, distToRight);
        
            let targetX, targetY;
        
            const randomPerpOffset = (Math.random() - 0.5) * 40;
            const randomOvershoot = 10 + Math.random() * 20;
            const randomRotation = (Math.random() - 0.5) * 90;
        
            if (minDist === distToTop) {
              targetY = -(el.offsetHeight / window.innerHeight * 100 + randomOvershoot);
              targetX = currentX + randomPerpOffset;
            } else if (minDist === distToBottom) {
              targetY = 100 + randomOvershoot;
              targetX = currentX + randomPerpOffset;
            } else if (minDist === distToLeft) {
              targetX = -(el.offsetWidth / window.innerWidth * 100 + randomOvershoot);
              targetY = currentY + randomPerpOffset;
            } else {
              targetX = 100 + randomOvershoot;
              targetY = currentY + randomPerpOffset;
            }
        
            el.style.transition = 'top 0.5s ease-out, left 0.5s ease-out, transform 0.5s ease-out';
            el.style.top = `${targetY}%`;
            el.style.left = `${targetX}%`;
            el.style.transform = `rotate(${photo.rotation + randomRotation}deg) scale(1.1)`;
        
            el.style.pointerEvents = 'none';
            }
        }}
        on:click={(e) => {
          // Get the clicked element
          const el = e.currentTarget;
      
          const currentX = photo.x;
          const currentY = photo.y;
      
          const distToTop = currentY;
          const distToBottom = 100 - currentY;
          const distToLeft = currentX;
          const distToRight = 100 - currentX;
      
          const minDist = Math.min(distToTop, distToBottom, distToLeft, distToRight);
      
          let targetX, targetY;
      
          const randomPerpOffset = (Math.random() - 0.5) * 40;
          const randomOvershoot = 10 + Math.random() * 20;
          const randomRotation = (Math.random() - 0.5) * 90;
      
          if (minDist === distToTop) {
            targetY = -(el.offsetHeight / window.innerHeight * 100 + randomOvershoot);
            targetX = currentX + randomPerpOffset;
          } else if (minDist === distToBottom) {
            targetY = 100 + randomOvershoot;
            targetX = currentX + randomPerpOffset;
          } else if (minDist === distToLeft) {
            targetX = -(el.offsetWidth / window.innerWidth * 100 + randomOvershoot);
            targetY = currentY + randomPerpOffset;
          } else {
            targetX = 100 + randomOvershoot;
            targetY = currentY + randomPerpOffset;
          }
      
          el.style.transition = 'top 0.5s ease-out, left 0.5s ease-out, transform 0.5s ease-out';
          el.style.top = `${targetY}%`;
          el.style.left = `${targetX}%`;
          el.style.transform = `rotate(${photo.rotation + randomRotation}deg) scale(1.1)`;
      
          el.style.pointerEvents = 'none';
      
        }}
			>
				<img
					src={photo.src}
					alt={'A photo from Rachy & Davey'}
					class="object-cover bg-gray-100"
				/>
			</div>
		{/each}
	</div>
</div>

<style lang="postcss">
	.polaroid-container {
		width: 25vw;
		max-width: 220px;
		min-width: 120px;
	}

	@import url('https://fonts.googleapis.com/css2?family=Kalam:wght@700&display=swap');
	h1 {
		font-family: 'Kalam', cursive;
    text-shadow: -4px 0 white, 0 4px white, 4px 0 white, 0 -4px white;
	}

  h1::before {
    content: '';
    position: absolute;
    top: -20px; /* Adjust padding around the text */
    left: -40px; /* Adjust padding around the text */
    right: -40px; /* Adjust padding around the text */
    bottom: -40px; /* Adjust padding around the text */
    background-color: rgba(203, 178, 178, 0.0); /* White background with 50% opacity */
    backdrop-filter: blur(3.5px); /* Adjust blur strength as needed */
    -webkit-backdrop-filter: blur(0.5px); /* For Safari support */
    border-radius: 8px; /* Match or adjust border-radius */
    z-index: -1; /* Place behind the text */
  }
</style>
