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
  RoundedBox,
  Torus,
  Cone
} from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';

// 3D Doctor Avatar
const DoctorAvatar = ({ isAnalyzing, emergencyLevel = 'normal' }) => {
  const avatarRef = useRef();
  const stethoscopeRef = useRef();
  const auraRef = useRef();
  
  useFrame((state) => {
    if (avatarRef.current) {
      avatarRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
      if (isAnalyzing) {
        avatarRef.current.position.y = Math.sin(state.clock.elapsedTime * 2) * 0.1;
      }
    }
    
    if (stethoscopeRef.current) {
      stethoscopeRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 1.5) * 0.1;
    }
    
    if (auraRef.current) {
      auraRef.current.rotation.y = state.clock.elapsedTime * 0.5;
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.1;
      auraRef.current.scale.setScalar(scale);
    }
  });

  const emergencyColors = {
    normal: "#4299e1",
    urgent: "#f6ad55",
    emergency: "#e53e3e"
  };

  return (
    <group ref={avatarRef} position={[0, 0, 0]}>
      {/* Doctor's Aura */}
      <group ref={auraRef}>
        <Torus args={[2, 0.05, 8, 32]} position={[0, 0, 0]}>
          <meshStandardMaterial 
            color={emergencyColors[emergencyLevel]} 
            transparent 
            opacity={0.6}
            emissive={emergencyColors[emergencyLevel]}
            emissiveIntensity={0.3}
          />
        </Torus>
      </group>
      
      {/* Doctor's Head */}
      <Sphere args={[0.6]} position={[0, 1.5, 0]}>
        <meshStandardMaterial 
          color="#f7fafc" 
          metalness={0.1} 
          roughness={0.8}
        />
      </Sphere>
      
      {/* Doctor's Body */}
      <Box args={[0.8, 1.2, 0.4]} position={[0, 0.2, 0]}>
        <meshStandardMaterial 
          color="#ffffff" 
          metalness={0.1} 
          roughness={0.9}
        />
      </Box>
      
      {/* Stethoscope */}
      <group ref={stethoscopeRef} position={[0, 0.5, 0.3]}>
        <Cylinder args={[0.02, 0.02, 0.8]} rotation={[0, 0, Math.PI / 6]}>
          <meshStandardMaterial color="#2d3748" metalness={0.8} roughness={0.2} />
        </Cylinder>
        <Cylinder args={[0.15, 0.15, 0.05]} position={[0, -0.5, 0]}>
          <meshStandardMaterial color="#1a202c" metalness={0.9} roughness={0.1} />
        </Cylinder>
      </group>
      
      {/* Doctor's Hat */}
      <Cylinder args={[0.4, 0.5, 0.2]} position={[0, 1.9, 0]}>
        <meshStandardMaterial color="#ffffff" />
      </Cylinder>
      
      {/* Medical Cross */}
      <group position={[0, 1.5, 0.65]}>
        <Box args={[0.1, 0.3, 0.05]}>
          <meshStandardMaterial color="#e53e3e" emissive="#742a2a" emissiveIntensity={0.3} />
        </Box>
        <Box args={[0.3, 0.1, 0.05]}>
          <meshStandardMaterial color="#e53e3e" emissive="#742a2a" emissiveIntensity={0.3} />
        </Box>
      </group>
      
      {/* Analysis Status Light */}
      <Float speed={3} rotationIntensity={0.5} floatIntensity={1}>
        <Sphere args={[0.1]} position={[0.8, 1.5, 0]}>
          <meshStandardMaterial 
            color={isAnalyzing ? "#48bb78" : "#718096"} 
            emissive={isAnalyzing ? "#22543d" : "#2d3748"}
            emissiveIntensity={0.5}
          />
        </Sphere>
      </Float>
    </group>
  );
};

// Medical Analysis Visualization
const AnalysisVisualization = ({ isAnalyzing, progress = 0, analysisData }) => {
  const dataRef = useRef();
  const particlesRef = useRef();
  
  useFrame((state) => {
    if (dataRef.current && isAnalyzing) {
      dataRef.current.rotation.y = state.clock.elapsedTime * 0.8;
    }
    
    if (particlesRef.current) {
      particlesRef.current.children.forEach((particle, index) => {
        particle.position.y += 0.01;
        if (particle.position.y > 5) {
          particle.position.y = -5;
        }
        particle.rotation.x += 0.02;
        particle.rotation.y += 0.01;
      });
    }
  });

  return (
    <group position={[0, 0, -3]}>
      {/* Analysis Data Stream */}
      {isAnalyzing && (
        <group ref={dataRef}>
          {[...Array(20)].map((_, index) => (
            <Box 
              key={index} 
              args={[0.1, 0.1, 0.1]} 
              position={[
                Math.cos(index * 0.3) * 3,
                Math.sin(index * 0.5) * 2,
                Math.sin(index * 0.2) * 2
              ]}
            >
              <meshStandardMaterial 
                color="#4299e1" 
                transparent 
                opacity={0.8}
                emissive="#1a365d"
                emissiveIntensity={0.3}
              />
            </Box>
          ))}
        </group>
      )}
      
      {/* Medical Particles */}
      <group ref={particlesRef}>
        {[...Array(50)].map((_, index) => (
          <Sphere 
            key={index} 
            args={[0.02]} 
            position={[
              (Math.random() - 0.5) * 10,
              (Math.random() - 0.5) * 10,
              (Math.random() - 0.5) * 10
            ]}
          >
            <meshStandardMaterial 
              color="#48bb78" 
              transparent 
              opacity={0.6}
              emissive="#22543d"
              emissiveIntensity={0.2}
            />
          </Sphere>
        ))}
      </group>
      
      {/* Progress Ring */}
      <Torus args={[1.5, 0.1, 8, 32]} position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial 
          color="#4299e1" 
          transparent 
          opacity={0.5}
          emissive="#1a365d"
          emissiveIntensity={0.2}
        />
      </Torus>
    </group>
  );
};

// Diagnosis Result Display
const DiagnosisDisplay = ({ diagnosis, isVisible }) => {
  const displayRef = useRef();
  
  useFrame((state) => {
    if (displayRef.current) {
      displayRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.1;
    }
  });

  if (!isVisible || !diagnosis) return null;

  return (
    <group ref={displayRef} position={[0, 0, 2]}>
      {/* Diagnosis Panel */}
      <RoundedBox args={[4, 3, 0.1]} radius={0.2} smoothness={4}>
        <meshStandardMaterial 
          color="#1a202c" 
          metalness={0.8} 
          roughness={0.2}
          transparent
          opacity={0.9}
        />
      </RoundedBox>
      
      {/* Diagnosis Title */}
      <Text
        position={[0, 1, 0.1]}
        fontSize={0.4}
        color="#4299e1"
        anchorX="center"
        anchorY="middle"
        font="/fonts/Inter-Bold.woff"
      >
        🏥 Doctor's Analysis
      </Text>
      
      {/* Diagnosis Content */}
      <Text
        position={[0, 0, 0.1]}
        fontSize={0.2}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        font="/fonts/Inter-Regular.woff"
        maxWidth={3.5}
      >
        {diagnosis.substring(0, 200) + (diagnosis.length > 200 ? '...' : '')}
      </Text>
      
      {/* Holographic Effect */}
      <Float speed={1} rotationIntensity={0.1} floatIntensity={0.3}>
        <Torus args={[2.2, 0.02, 8, 32]} position={[0, 0, -0.1]}>
          <meshStandardMaterial 
            color="#4299e1" 
            emissive="#1a365d"
            emissiveIntensity={0.3}
            transparent
            opacity={0.7}
          />
        </Torus>
      </Float>
    </group>
  );
};

// Doctor Analysis Scene
const DoctorAnalysisScene = ({ isAnalyzing, progress, emergencyLevel, diagnosis }) => {
  return (
    <>
      <Environment preset="studio" />
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={1} />
      <pointLight position={[-5, 5, 5]} intensity={0.5} color="#4299e1" />
      
      <DoctorAvatar 
        isAnalyzing={isAnalyzing} 
        emergencyLevel={emergencyLevel} 
      />
      
      <AnalysisVisualization 
        isAnalyzing={isAnalyzing} 
        progress={progress} 
      />
      
      <DiagnosisDisplay 
        diagnosis={diagnosis} 
        isVisible={!isAnalyzing && diagnosis} 
      />
      
      {/* Status Text */}
      <Float speed={1} rotationIntensity={0.1} floatIntensity={0.3}>
        <Text
          position={[0, -3, 0]}
          fontSize={0.4}
          color={isAnalyzing ? "#f6ad55" : "#4299e1"}
          anchorX="center"
          anchorY="middle"
          font="/fonts/Inter-Bold.woff"
        >
          {isAnalyzing ? "🔬 Analyzing symptoms..." : "✅ Analysis complete"}
        </Text>
      </Float>
    </>
  );
};

// Main Doctor Analysis Canvas
const DoctorAnalysis3DCanvas = ({ isAnalyzing, progress = 0, emergencyLevel = 'normal', diagnosis, isVisible }) => {
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
        camera={{ position: [0, 2, 8], fov: 75 }}
      >
        <DoctorAnalysisScene 
          isAnalyzing={isAnalyzing} 
          progress={progress}
          emergencyLevel={emergencyLevel}
          diagnosis={diagnosis}
        />
        <OrbitControls 
          enableZoom={false} 
          enablePan={false} 
          autoRotate={isAnalyzing} 
          autoRotateSpeed={0.5}
          enableDamping
          dampingFactor={0.05}
        />
      </Canvas>
    </div>
  );
};

export default DoctorAnalysis3DCanvas;
