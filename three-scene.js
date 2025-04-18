// Scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111111);
scene.fog = new THREE.Fog(0x111111, 10, 100);

// Camera
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 20, 50);

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.domElement.tabIndex = 1;
document.body.appendChild(renderer.domElement);

// Label Renderer
const labelRenderer = new THREE.CSS2DRenderer();
labelRenderer.setSize(window.innerWidth, window.innerHeight);
labelRenderer.domElement.style.position = 'absolute';
labelRenderer.domElement.style.top = '0px';
labelRenderer.domElement.className = 'labelRenderer';
document.body.appendChild(labelRenderer.domElement);

// Controls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

// Lights
scene.add(new THREE.AmbientLight(0xffffff, 0.3));
const pointLight = new THREE.PointLight(0xffffff, 1.2);
pointLight.position.set(10, 20, 20);
scene.add(pointLight);

// Ground
const ground = new THREE.Mesh(
  new THREE.CircleGeometry(60, 64),
  new THREE.MeshStandardMaterial({ color: 0x222222, side: THREE.DoubleSide })
);
ground.rotation.x = -Math.PI / 2;
scene.add(ground);

// Load JSONL
async function loadScene() {
  // Remove previously rendered towers and labels
  scene.children
    .filter(obj => obj.name === 'liquidityTower')
    .forEach(obj => scene.remove(obj));
  const res = await fetch('data/price_log.jsonl');
  const text = await res.text();
  const lines = text.trim().split('\n').map(line => JSON.parse(line));

  const pairMap = {
    'SHT/USDC': { x: -20, color: 0x00ffff },       // Cyan
    'SHT/ETH': { x: 0, color: 0xcc3300 },          // Brick red / orange
    'SHT/POL': { x: 20, color: 0x4b0082 },         // Deep purple (Indigo)
  };

  const latestEntries = {};
  lines.forEach(entry => {
    if (!latestEntries[entry.pair] || new Date(entry.timestamp) > new Date(latestEntries[entry.pair].timestamp)) {
      latestEntries[entry.pair] = entry;
    }
  });
  
  Object.values(latestEntries).forEach(entry => {
    const pairInfo = pairMap[entry.pair];
    const price = entry.price_usdc_per_sht || entry.price_eth_per_sht || entry.price_pol_per_sht;
    const liquidity = entry.liquidity;

    if (!pairInfo || price == null || liquidity == null) return;

    let height = 5;

    if (entry.pair === 'SHT/USDC') {
      height = price;
    } else if (entry.pair === 'SHT/ETH' && entry.eth_usd) {
      height = price * entry.eth_usd;
    } else if (entry.pair === 'SHT/POL' && entry.pol_usd) {
      height = price * entry.pol_usd;
    } else {
      console.warn(`Missing price conversion for ${entry.pair}`);
    }

    console.log(`${entry.pair} | price: ${price} | height: ${height}`);

    let liquidityInUSD = 0;
    
    if (entry.pair === 'SHT/USDC') {
      liquidityInUSD = liquidity / 1e6; // USDC has 6 decimals
    } else if (entry.pair === 'SHT/ETH' && entry.eth_usd) {
      liquidityInUSD = (liquidity / 1e18) * entry.eth_usd;
    } else if (entry.pair === 'SHT/POL' && entry.pol_usd) {
      liquidityInUSD = (liquidity / 1e18) * entry.pol_usd;
    }
    
    const radius = Math.log10(liquidityInUSD + 1) * 1.0;
    console.log(`${entry.pair} | USD: ${liquidityInUSD.toFixed(2)} | radius: ${radius.toFixed(2)}`);

    const geometry = new THREE.CylinderGeometry(radius, radius, height, 32);
    const material = new THREE.MeshStandardMaterial({
      color: pairInfo.color,
      emissive: pairInfo.color,
      emissiveIntensity: 0.6,
      transparent: true,
      opacity: 0.4,
      metalness: 0.5,
      roughness: 0.2
    });
    const cube = new THREE.Mesh(geometry, material);
    cube.name = 'liquidityTower';
    cube.position.set(pairInfo.x, height / 2, price * 50);
    scene.add(cube);

    const priceLabelDiv = document.createElement('div');
    priceLabelDiv.className = 'label';
    priceLabelDiv.innerHTML = `<strong>${entry.pair}</strong><br/>$${height.toFixed(4)} USD`;
    priceLabelDiv.style.color = 'white';
    priceLabelDiv.style.fontSize = '0.8em';
    priceLabelDiv.style.textAlign = 'center';
    priceLabelDiv.style.backgroundColor = 'rgba(0,0,0,0.5)';
    priceLabelDiv.style.padding = '2px 6px';
    priceLabelDiv.style.borderRadius = '4px';

    const priceLabel = new THREE.CSS2DObject(priceLabelDiv);
    priceLabel.position.set(0, height + 1.5, 0);
    cube.add(priceLabel);

    const baseLabelDiv = document.createElement('div');
    baseLabelDiv.className = 'label';
    baseLabelDiv.textContent = `Liquidity: $${liquidityInUSD.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
    baseLabelDiv.style.color = 'gray';
    baseLabelDiv.style.fontSize = '0.7em';
    baseLabelDiv.style.textAlign = 'center';
    baseLabelDiv.style.backgroundColor = 'rgba(0,0,0,0.4)';
    baseLabelDiv.style.padding = '2px 6px';
    baseLabelDiv.style.borderRadius = '4px';

    const baseLabel = new THREE.CSS2DObject(baseLabelDiv);
    baseLabel.position.set(0, -0.5, 0);
    cube.add(baseLabel);
  });
}
loadScene();

// Animate
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}
animate();

// Resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// Pointer Event Test
renderer.domElement.addEventListener('pointerdown', () => {
  console.log('pointerdown received by renderer');
});