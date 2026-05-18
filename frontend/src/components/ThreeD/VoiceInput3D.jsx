import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { 
  Text, 
  Html, 
  Sphere, 
  Box, 
  Cylinder,
  Float,
  Environment,
  OrbitControls,
  MeshWobbleGeometry,
  MeshDistortMaterial
} from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';

// 3D Microphone Component
const AnimatedMicrophone = ({ isRecording, volume = 0 }) => {
  const micRef = useRef();
  const standRef = useRef();
  const volumeRingsRef = useRef([]);
  
  useFrame((state) => {
    if (micRef.current) {
      const pulse = isRecording ? 1 + Math.sin(state.clock.elapsedTime * 3) * 0.1 : 1;
      micRef.current.scale.setScalar(pulse);
    }
    
    if (standRef.current) {
      standRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
    }
    
    // Animate volume rings
    volumeRingsRef.current.forEach((ring, index) => {
      if (ring && isRecording) {
        const scale = 1 + (volume * 0.1 + Math.sin(state.clock.elapsedTime * 2 + index) * 0.2);
        ring.scale.setScalar(scale);
        ring.material.opacity = 0.7 - (index * 0.1);
      }
    });
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Microphone Stand */}
      <group ref={standRef}>
        <Cylinder args={[0.05, 0.05, 2]} position={[0, -1, 0]}>
          <meshStandardMaterial color="#2d3748" metalness={0.8} roughness={0.2} />
        </Cylinder>
        
        {/* Microphone Head */}
        <group ref={micRef}>
          <Cylinder args={[0.3, 0.3, 0.8]} position={[0, 0.5, 0]}>
            <meshStandardMaterial 
              color={isRecording ? "#48bb78" : "#718096"} 
              metalness={0.9} 
              roughness={0.1}
              emissive={isRecording ? "#22543d" : "#1a202c"}
              emissiveIntensity={0.3}
            />
          </Cylinder>
          
          {/* Microphone Grille */}
          <Sphere args={[0.35]} position={[0, 0.9, 0]}>
            <meshStandardMaterial 
              color="#1a202c" 
              metalness={0.7} 
              roughness={0.3}
              wireframe={true}
            />
          </Sphere>
        </group>
      </group>
      
      {/* Volume Visualization Rings */}
      {isRecording && [1, 2, 3, 4].map((radius, index) => (
        <mesh 
          key={index} 
          ref={(el) => volumeRingsRef.current[index] = el}
          position={[0, 0.5, 0]}
        >
          <torusGeometry args={[radius, 0.05, 8, 32]} />
          <meshStandardMaterial 
            color="#4299e1" 
            transparent 
            opacity={0.6 - index * 0.1}
            emissive="#1a365d"
            emissiveIntensity={0.2}
          />
        </mesh>
      ))}
      
      {/* Status Indicator */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
        <Sphere args={[0.1]} position={[0, 1.5, 0]}>
          <meshStandardMaterial 
            color={isRecording ? "#48bb78" : "#718096"} 
            emissive={isRecording ? "#22543d" : "#2d3748"}
            emissiveIntensity={0.5}
          />
        </Sphere>
      </Float>
    </group>
  );
};

// Sound Wave Visualization
const SoundWaves = ({ isRecording, volume = 0 }) => {
  const waveRefs = useRef([]);
  
  useFrame((state) => {
    if (isRecording) {
      waveRefs.current.forEach((wave, index) => {
        if (wave) {
          const offset = index * 0.5;
          const scale = 1 + Math.sin(state.clock.elapsedTime * 3 + offset) * (volume * 0.5 + 0.2);
          wave.scale.x = scale;
          wave.material.opacity = 0.8 - (index * 0.1);
        }
      });
    }
  });

  if (!isRecording) return null;

  return (
    <group position={[0, 0, -2]}>
      {[1, 2, 3, 4, 5].map((index) => (
        <mesh 
          key={index} 
          ref={(el) => waveRefs.current[index] = el}
          position={[0, 0, index * 0.2]}
        >
          <planeGeometry args={[6, 0.1]} />
          <meshStandardMaterial 
            color="#4299e1" 
            transparent 
            opacity={0.6}
            emissive="#1a365d"
            emissiveIntensity={0.2}
          />
        </mesh>
      ))}
    </group>
  );
};

// Voice Input 3D Scene
const VoiceInputScene = ({ isRecording, volume }) => {
  return (
    <>
      <Environment preset="studio" />
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={1} />
      <pointLight position={[-5, 5, 5]} intensity={0.5} color="#4299e1" />
      
      <AnimatedMicrophone isRecording={isRecording} volume={volume} />
      <SoundWaves isRecording={isRecording} volume={volume} />
      
      {/* Recording Status Text */}
      <Float speed={1} rotationIntensity={0.1} floatIntensity={0.3}>
        <Text
          position={[0, -2.5, 0]}
          fontSize={0.4}
          color={isRecording ? "#48bb78" : "#718096"}
          anchorX="center"
          anchorY="middle"
          font="/fonts/Inter-Bold.woff"
        >
          {isRecording ? "🎤 Recording..." : "🎤 Ready to Record"}
        </Text>
      </Float>
    </>
  );
};

// Main Voice Input Canvas
const VoiceInput3DCanvas = ({ isRecording, volume = 0, isVisible }) => {
  if (!isVisible) return null;
  
  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      zIndex: 1,
      pointerEvents: 'none'
    }}>
      <Canvas
        style={{
          width: '100%',
          height: '100%'
        }}
        camera={{ position: [0, 2, 6], fov: 75 }}
      >
        <VoiceInputScene isRecording={isRecording} volume={volume} />
        <OrbitControls 
          enableZoom={false} 
          enablePan={false} 
          autoRotate={isRecording} 
          autoRotateSpeed={0.5}
          enableDamping
          dampingFactor={0.05}
        />
      </Canvas>
    </div>
  );
};

export default VoiceInput3DCanvas;
