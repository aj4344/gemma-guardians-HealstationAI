import React, { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial, Sphere, Float, Text } from '@react-three/drei';
import * as THREE from 'three';

// Medical Particle System
const MedicalParticleSystem = ({ count = 1000, isActive = true }) => {
  const points = useRef();
  const [positions, colors] = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      // Random positions in a sphere
      const radius = Math.random() * 10 + 5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
      
      // Medical-themed colors
      const color = new THREE.Color();
      const colorOptions = [
        '#4299e1', // Blue
        '#48bb78', // Green
        '#f6ad55', // Orange
        '#805ad5', // Purple
        '#e53e3e'  // Red
      ];
      color.set(colorOptions[Math.floor(Math.random() * colorOptions.length)]);
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    
    return [positions, colors];
  }, [count]);

  useFrame((state) => {
    if (points.current && isActive) {
      points.current.rotation.x = state.clock.elapsedTime * 0.05;
      points.current.rotation.y = state.clock.elapsedTime * 0.1;
      
      // Pulse effect
      const scale = 1 + Math.sin(state.clock.elapsedTime) * 0.1;
      points.current.scale.setScalar(scale);
    }
  });

  return (
    <Points ref={points} positions={positions} colors={colors}>
      <PointMaterial
        transparent
        vertexColors
        size={0.05}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </Points>
  );
};

// Floating Medical Symbols
const FloatingSymbols = ({ isActive = true }) => {
  const symbols = ['🩺', '💊', '🏥', '🔬', '💉', '🧬'];
  const symbolRefs = useRef([]);
  
  useFrame((state) => {
    if (isActive) {
      symbolRefs.current.forEach((symbol, index) => {
        if (symbol) {
          symbol.position.y = Math.sin(state.clock.elapsedTime * 0.5 + index) * 2;
          symbol.rotation.y = state.clock.elapsedTime * 0.3;
        }
      });
    }
  });

  return (
    <group>
      {symbols.map((symbol, index) => (
        <Float key={index} speed={1 + index * 0.2} rotationIntensity={0.3} floatIntensity={0.5}>
          <Text
            ref={(el) => (symbolRefs.current[index] = el)}
            position={[
              Math.cos(index * Math.PI * 2 / symbols.length) * 8,
              0,
              Math.sin(index * Math.PI * 2 / symbols.length) * 8
            ]}
            fontSize={1}
            color="#ffffff"
            anchorX="center"
            anchorY="middle"
          >
            {symbol}
          </Text>
        </Float>
      ))}
    </group>
  );
};

// Main Interactive Medical Environment
const InteractiveMedicalEnvironment = ({ stage = 'idle', isActive = true }) => {
  const environmentRef = useRef();
  
  useFrame((state) => {
    if (environmentRef.current) {
      environmentRef.current.rotation.y = state.clock.elapsedTime * 0.02;
    }
  });

  const stageColors = {
    idle: '#4299e1',
    recording: '#48bb78',
    analyzing: '#f6ad55',
    diagnosis: '#805ad5',
    emergency: '#e53e3e'
  };

  return (
    <group ref={environmentRef}>
      <MedicalParticleSystem count={800} isActive={isActive} />
      <FloatingSymbols isActive={isActive} />
      
      {/* Central Health Symbol */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
        <Sphere args={[0.5]} position={[0, 0, 0]}>
          <meshStandardMaterial
            color={stageColors[stage]}
            emissive={stageColors[stage]}
            emissiveIntensity={0.3}
            transparent
            opacity={0.8}
          />
        </Sphere>
      </Float>
      
      {/* Stage Status */}
      <Float speed={1} rotationIntensity={0.1} floatIntensity={0.3}>
        <Text
          position={[0, -3, 0]}
          fontSize={0.5}
          color={stageColors[stage]}
          anchorX="center"
          anchorY="middle"
          font="/fonts/Inter-Bold.woff"
        >
          {stage.toUpperCase()}
        </Text>
      </Float>
    </group>
  );
};

// Enhanced Medical Canvas with Interactive Environment
const EnhancedMedicalCanvas = ({ stage = 'idle', isActive = true, opacity = 0.8 }) => {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      zIndex: -1,
      pointerEvents: 'none',
      opacity: opacity
    }}>
      <Canvas
        style={{
          width: '100%',
          height: '100%'
        }}
        camera={{ position: [0, 0, 15], fov: 75 }}
      >
        <ambientLight intensity={0.3} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <pointLight position={[-10, -10, -5]} intensity={0.5} />
        
        <InteractiveMedicalEnvironment stage={stage} isActive={isActive} />
        
        <fog attach="fog" args={['#000000', 10, 30]} />
      </Canvas>
    </div>
  );
};

export default EnhancedMedicalCanvas;
