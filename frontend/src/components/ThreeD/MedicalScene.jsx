import React, { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { 
  Text, 
  Float, 
  Html, 
  OrbitControls, 
  Environment, 
  PerspectiveCamera,
  useGLTF,
  Sphere,
  Box,
  Cylinder,
  Torus,
  Stars,
  Cloud,
  Sky
} from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';

// Animated Medical Stethoscope (no MeshWobbleGeometry)
const AnimatedStethoscope = ({ position = [0, 0, 0], scale = 1 }) => {
  const groupRef = useRef();
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
      groupRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 0.8) * 0.2;
    }
  });
  return (
    <group ref={groupRef} position={position} scale={scale}>
      {/* Stethoscope body */}
      <Cylinder args={[0.05, 0.05, 2]} position={[0, 0, 0]} rotation={[0, 0, Math.PI / 6]}>
        <meshStandardMaterial color="#2d3748" metalness={0.8} roughness={0.2} />
      </Cylinder>
      {/* Earpieces */}
      <Sphere args={[0.08]} position={[-0.8, 0.8, 0]}>
        <meshStandardMaterial color="#4a5568" metalness={0.9} roughness={0.1} />
      </Sphere>
      <Sphere args={[0.08]} position={[0.8, 0.8, 0]}>
        <meshStandardMaterial color="#4a5568" metalness={0.9} roughness={0.1} />
      </Sphere>
      {/* Chest piece */}
      <Cylinder args={[0.3, 0.3, 0.1]} position={[0, -1, 0]}>
        <meshStandardMaterial color="#1a202c" metalness={0.7} roughness={0.3} />
      </Cylinder>
      {/* Connecting tubes */}
      <Cylinder args={[0.02, 0.02, 1.2]} position={[-0.4, 0.2, 0]} rotation={[0, 0, Math.PI / 4]}>
        <meshStandardMaterial color="#718096" />
      </Cylinder>
      <Cylinder args={[0.02, 0.02, 1.2]} position={[0.4, 0.2, 0]} rotation={[0, 0, -Math.PI / 4]}>
        <meshStandardMaterial color="#718096" />
      </Cylinder>
    </group>
  );
};

// Floating Medical Icons
const FloatingMedicalIcon = ({ position, icon, color = "#4299e1", scale = 0.5 }) => {
  const meshRef = useRef();
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.7) * 0.2;
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 0.6 + position[0]) * 0.5;
    }
  });

  const geometry = useMemo(() => {
    switch (icon) {
      case 'heart':
        return <Sphere args={[0.3]} />;
      case 'brain':
        return <Box args={[0.5, 0.4, 0.3]} />;
      case 'pill':
        return <Cylinder args={[0.15, 0.15, 0.6]} />;
      case 'cross':
        return (
          <group>
            <Box args={[0.1, 0.8, 0.1]} />
            <Box args={[0.8, 0.1, 0.1]} />
          </group>
        );
      default:
        return <Sphere args={[0.3]} />;
    }
  }, [icon]);

  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
      <mesh ref={meshRef} position={position} scale={scale}>
        {geometry}
        <meshStandardMaterial 
          color={color} 
          metalness={0.5} 
          roughness={0.2} 
          transparent 
          opacity={0.8}
        />
      </mesh>
    </Float>
  );
};

// Animated DNA Helix
const DNAHelix = ({ position = [0, 0, 0], scale = 1 }) => {
  const groupRef = useRef();
  const helixRef = useRef();
  
  useFrame((state) => {
    if (helixRef.current) {
      helixRef.current.rotation.y = state.clock.elapsedTime * 0.3;
    }
  });

  const helixPoints = useMemo(() => {
    const points = [];
    for (let i = 0; i < 50; i++) {
      const angle = (i / 50) * Math.PI * 8;
      const x = Math.cos(angle) * 0.5;
      const z = Math.sin(angle) * 0.5;
      const y = (i / 50) * 4 - 2;
      points.push([x, y, z]);
    }
    return points;
  }, []);

  return (
    <group ref={groupRef} position={position} scale={scale}>
      <group ref={helixRef}>
        {helixPoints.map((point, index) => (
          <Sphere key={index} args={[0.08]} position={point}>
            <meshStandardMaterial 
              color={index % 2 === 0 ? "#4299e1" : "#48bb78"} 
              emissive={index % 2 === 0 ? "#1a365d" : "#22543d"}
              emissiveIntensity={0.3}
            />
          </Sphere>
        ))}
      </group>
    </group>
  );
};

// Pulsing Heart Animation
const PulsingHeart = ({ position = [0, 0, 0], scale = 1 }) => {
  const heartRef = useRef();
  
  useFrame((state) => {
    if (heartRef.current) {
      const pulse = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.2;
      heartRef.current.scale.setScalar(pulse * scale);
    }
  });

  return (
    <mesh ref={heartRef} position={position}>
      <Sphere args={[0.4]}>
        <meshStandardMaterial 
          color="#e53e3e" 
          emissive="#742a2a" 
          emissiveIntensity={0.3}
          metalness={0.1}
          roughness={0.8}
        />
      </Sphere>
    </mesh>
  );
};

// Medical Particle System
const MedicalParticles = () => {
  const particlesRef = useRef();
  
  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < 100; i++) {
      temp.push({
        position: [
          (Math.random() - 0.5) * 20,
          (Math.random() - 0.5) * 20,
          (Math.random() - 0.5) * 20
        ],
        scale: Math.random() * 0.5 + 0.1,
        speed: Math.random() * 0.02 + 0.01
      });
    }
    return temp;
  }, []);

  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.children.forEach((particle, index) => {
        particle.position.y += particles[index].speed;
        if (particle.position.y > 10) {
          particle.position.y = -10;
        }
        particle.rotation.x += 0.01;
        particle.rotation.y += 0.01;
      });
    }
  });

  return (
    <group ref={particlesRef}>
      {particles.map((particle, index) => (
        <mesh key={index} position={particle.position} scale={particle.scale}>
          <Sphere args={[0.05]}>
            <meshStandardMaterial 
              color="#4299e1" 
              transparent 
              opacity={0.6}
              emissive="#1a365d"
              emissiveIntensity={0.2}
            />
          </Sphere>
        </mesh>
      ))}
    </group>
  );
};

// Interactive Medical Dashboard
const MedicalDashboard = ({ isRecording, isAnalyzing, language }) => {
  const dashboardRef = useRef();
  
  useFrame((state) => {
    if (dashboardRef.current) {
      dashboardRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.1;
    }
  });

  return (
    <group ref={dashboardRef} position={[0, 0, 0]}>
      {/* Main Dashboard Panel */}
      <Box args={[4, 2.5, 0.1]} position={[0, 0, 0]}>
        <meshStandardMaterial 
          color="#1a202c" 
          metalness={0.8} 
          roughness={0.2}
          transparent
          opacity={0.9}
        />
      </Box>
      
      {/* Status Indicators */}
      <Sphere args={[0.1]} position={[-1.5, 0.8, 0.1]}>
        <meshStandardMaterial 
          color={isRecording ? "#48bb78" : "#718096"} 
          emissive={isRecording ? "#22543d" : "#2d3748"}
          emissiveIntensity={0.5}
        />
      </Sphere>
      
      <Sphere args={[0.1]} position={[0, 0.8, 0.1]}>
        <meshStandardMaterial 
          color={isAnalyzing ? "#f6ad55" : "#718096"} 
          emissive={isAnalyzing ? "#c05621" : "#2d3748"}
          emissiveIntensity={0.5}
        />
      </Sphere>
      
      {/* Language Indicator */}
      <Text
        position={[0, -0.5, 0.1]}
        fontSize={0.3}
        color="#4299e1"
        anchorX="center"
        anchorY="middle"
        font="/fonts/Inter-Bold.woff"
      >
        {language?.toUpperCase() || 'EN'}
      </Text>
      
      {/* Holographic Display Effect */}
      <Torus args={[2.2, 0.02, 8, 32]} position={[0, 0, -0.1]}>
        <meshStandardMaterial 
          color="#4299e1" 
          emissive="#1a365d"
          emissiveIntensity={0.3}
          transparent
          opacity={0.7}
        />
      </Torus>
    </group>
  );
};

// Main Medical Scene Component
const MedicalScene = ({ isRecording, isAnalyzing, language, theme }) => {
  const { camera } = useThree();
  
  useEffect(() => {
    if (camera) {
      camera.position.set(0, 2, 8);
      camera.lookAt(0, 0, 0);
    }
  }, [camera]);

  return (
    <>
      {/* Environment and Lighting */}
      <Environment preset="studio" />
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={1} />
      <pointLight position={[-5, 5, 5]} intensity={0.5} color="#4299e1" />
      
      {/* Background Elements */}
      <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
      
      {/* Medical Particle System */}
      <MedicalParticles />
      
      {/* Main Medical Elements */}
      <AnimatedStethoscope position={[-3, 1, 0]} scale={0.8} />
      <DNAHelix position={[3, 0, 0]} scale={0.6} />
      <PulsingHeart position={[0, 2, -2]} scale={0.8} />
      
      {/* Interactive Dashboard */}
      <MedicalDashboard 
        isRecording={isRecording} 
        isAnalyzing={isAnalyzing} 
        language={language} 
      />
      
      {/* Floating Medical Icons */}
      <FloatingMedicalIcon 
        position={[-4, -1, 2]} 
        icon="heart" 
        color="#e53e3e" 
      />
      <FloatingMedicalIcon 
        position={[4, -1, 2]} 
        icon="brain" 
        color="#805ad5" 
      />
      <FloatingMedicalIcon 
        position={[-2, 3, 1]} 
        icon="pill" 
        color="#48bb78" 
      />
      <FloatingMedicalIcon 
        position={[2, 3, 1]} 
        icon="cross" 
        color="#4299e1" 
      />
      
      {/* Ambient Medical Equipment */}
      <Float speed={1} rotationIntensity={0.2} floatIntensity={0.5}>
        <Cylinder args={[0.3, 0.3, 1.5]} position={[-5, 0, -3]} rotation={[0, 0, Math.PI / 8]}>
          <meshStandardMaterial color="#2d3748" metalness={0.8} roughness={0.2} />
        </Cylinder>
      </Float>
      
      <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.8}>
        <Box args={[0.8, 0.5, 0.3]} position={[5, 0, -3]}>
          <meshStandardMaterial color="#1a202c" metalness={0.6} roughness={0.4} />
        </Box>
      </Float>
    </>
  );
};

// Main Canvas Component
const ThreeDMedicalCanvas = ({ isRecording, isAnalyzing, language, theme }) => {
  return (
    <Canvas
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -1,
        pointerEvents: 'none'
      }}
      camera={{ position: [0, 2, 8], fov: 75 }}
    >
      <MedicalScene 
        isRecording={isRecording} 
        isAnalyzing={isAnalyzing} 
        language={language} 
        theme={theme}
      />
      <OrbitControls 
        enableZoom={false} 
        enablePan={false} 
        autoRotate 
        autoRotateSpeed={0.5}
        enableDamping
        dampingFactor={0.05}
      />
    </Canvas>
  );
};

export default ThreeDMedicalCanvas;
