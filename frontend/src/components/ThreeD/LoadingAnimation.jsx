import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { 
  Text, 
  Html, 
  Sphere, 
  Box, 
  Float,
  Environment,
  OrbitControls
} from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';

// Enhanced Loading Spinner with 3D Medical Animation
const Medical3DLoader = ({ stage, progress = 0 }) => {
  const groupRef = useRef();
  const sphereRef = useRef();
  const ringRefs = useRef([]);
  
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.5;
    }
    
    if (sphereRef.current) {
      sphereRef.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 2) * 0.1);
    }
    
    ringRefs.current.forEach((ring, index) => {
      if (ring) {
        ring.rotation.x = state.clock.elapsedTime * (0.5 + index * 0.2);
        ring.rotation.z = state.clock.elapsedTime * (0.3 + index * 0.1);
      }
    });
  });

  const stageColors = {
    'analyzing': '#4299e1',
    'generating_diagnosis': '#f6ad55',
    'creating_audio': '#48bb78',
    'finalizing': '#805ad5'
  };

  return (
    <group ref={groupRef}>
      {/* Central Pulsing Core */}
      <mesh ref={sphereRef}>
        <Sphere args={[0.5]}>
          <meshStandardMaterial 
            color={stageColors[stage] || '#4299e1'} 
            emissive={stageColors[stage] || '#1a365d'}
            emissiveIntensity={0.3}
            transparent
            opacity={0.8}
          />
        </Sphere>
      </mesh>
      
      {/* Rotating Rings */}
      {[1, 2, 3].map((size, index) => (
        <mesh 
          key={index} 
          ref={(el) => ringRefs.current[index] = el}
          position={[0, 0, 0]}
        >
          <torusGeometry args={[size, 0.05, 8, 32]} />
          <meshStandardMaterial 
            color={stageColors[stage] || '#4299e1'} 
            transparent 
            opacity={0.6 - index * 0.1}
            emissive={stageColors[stage] || '#1a365d'}
            emissiveIntensity={0.2}
          />
        </mesh>
      ))}
      
      {/* Progress Indicator */}
      <Text
        position={[0, -2, 0]}
        fontSize={0.4}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        font="/fonts/Inter-Bold.woff"
      >
        {Math.round(progress)}%
      </Text>
      
      {/* Floating Medical Symbols */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
        <Text
          position={[2, 1, 0]}
          fontSize={0.8}
          color="#4299e1"
          anchorX="center"
          anchorY="middle"
        >
          +
        </Text>
      </Float>
      
      <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.8}>
        <mesh position={[-2, 1, 0]}>
          <Sphere args={[0.2]}>
            <meshStandardMaterial color="#48bb78" transparent opacity={0.7} />
          </Sphere>
        </mesh>
      </Float>
    </group>
  );
};

// 3D Loading Canvas Component
const ThreeDLoadingCanvas = ({ stage, progress, isVisible }) => {
  if (!isVisible) return null;
  
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      zIndex: 9999,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Canvas
        style={{
          width: '100%',
          height: '100%'
        }}
        camera={{ position: [0, 0, 8], fov: 75 }}
      >
        <Environment preset="studio" />
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <pointLight position={[-5, 5, 5]} intensity={0.5} color="#4299e1" />
        
        <Medical3DLoader stage={stage} progress={progress} />
        
        <OrbitControls 
          enableZoom={false} 
          enablePan={false} 
          autoRotate 
          autoRotateSpeed={1}
          enableDamping
          dampingFactor={0.05}
        />
      </Canvas>
      
      {/* HTML Overlay for Text */}
      <div style={{
        position: 'absolute',
        bottom: '20%',
        left: '50%',
        transform: 'translateX(-50%)',
        textAlign: 'center',
        color: 'white',
        fontSize: '1.5rem',
        fontWeight: 'bold',
        textShadow: '2px 2px 4px rgba(0,0,0,0.5)'
      }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {stage === 'analyzing' && "🔬 AI Doctor is analyzing..."}
          {stage === 'generating_diagnosis' && "🏥 Generating comprehensive diagnosis..."}
          {stage === 'creating_audio' && "🎵 Creating audio response..."}
          {stage === 'finalizing' && "✨ Finalizing presentation..."}
        </motion.div>
      </div>
    </div>
  );
};

export default ThreeDLoadingCanvas;
