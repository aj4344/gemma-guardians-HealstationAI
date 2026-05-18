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
  Plane,
  RoundedBox
} from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';

// 3D File Upload Zone
const FileUploadZone = ({ isDragOver, hasFiles, fileCount = 0 }) => {
  const zoneRef = useRef();
  const borderRef = useRef();
  
  useFrame((state) => {
    if (zoneRef.current) {
      const pulse = isDragOver ? 1.05 + Math.sin(state.clock.elapsedTime * 4) * 0.05 : 1;
      zoneRef.current.scale.setScalar(pulse);
    }
    
    if (borderRef.current) {
      borderRef.current.rotation.y = state.clock.elapsedTime * 0.5;
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Main Upload Zone */}
      <group ref={zoneRef}>
        <RoundedBox args={[4, 3, 0.1]} position={[0, 0, 0]} radius={0.2} smoothness={4}>
          <meshStandardMaterial 
            color={isDragOver ? "#4299e1" : hasFiles ? "#48bb78" : "#718096"} 
            transparent 
            opacity={0.3}
            emissive={isDragOver ? "#1a365d" : hasFiles ? "#22543d" : "#2d3748"}
            emissiveIntensity={0.2}
          />
        </RoundedBox>
        
        {/* Upload Icon */}
        <Box args={[0.1, 1, 0.1]} position={[0, 0.2, 0.1]}>
          <meshStandardMaterial 
            color={isDragOver ? "#4299e1" : hasFiles ? "#48bb78" : "#718096"} 
            emissive="#1a365d"
            emissiveIntensity={0.3}
          />
        </Box>
        <Box args={[0.6, 0.1, 0.1]} position={[0, 0.4, 0.1]}>
          <meshStandardMaterial 
            color={isDragOver ? "#4299e1" : hasFiles ? "#48bb78" : "#718096"} 
            emissive="#1a365d"
            emissiveIntensity={0.3}
          />
        </Box>
      </group>
      
      {/* Animated Border */}
      <group ref={borderRef}>
        <Cylinder args={[2.2, 2.2, 0.05, 32]} position={[0, 0, -0.1]}>
          <meshStandardMaterial 
            color={isDragOver ? "#4299e1" : "#718096"} 
            transparent 
            opacity={0.8}
            emissive="#1a365d"
            emissiveIntensity={0.2}
            wireframe={true}
          />
        </Cylinder>
      </group>
      
      {/* File Count Indicator */}
      {hasFiles && (
        <Float speed={2} rotationIntensity={0.3} floatIntensity={0.5}>
          <Sphere args={[0.3]} position={[1.5, 1, 0.2]}>
            <meshStandardMaterial 
              color="#48bb78" 
              emissive="#22543d"
              emissiveIntensity={0.3}
            />
          </Sphere>
          <Text
            position={[1.5, 1, 0.5]}
            fontSize={0.3}
            color="#ffffff"
            anchorX="center"
            anchorY="middle"
            font="/fonts/Inter-Bold.woff"
          >
            {fileCount}
          </Text>
        </Float>
      )}
      
      {/* Status Text */}
      <Float speed={1} rotationIntensity={0.1} floatIntensity={0.3}>
        <Text
          position={[0, -2, 0]}
          fontSize={0.4}
          color={isDragOver ? "#4299e1" : hasFiles ? "#48bb78" : "#718096"}
          anchorX="center"
          anchorY="middle"
          font="/fonts/Inter-Bold.woff"
        >
          {isDragOver ? "📁 Drop files here" : hasFiles ? "✅ Files ready" : "📁 Upload medical files"}
        </Text>
      </Float>
    </group>
  );
};

// 3D File Preview Cards
const FilePreviewCard = ({ file, index, position }) => {
  const cardRef = useRef();
  
  useFrame((state) => {
    if (cardRef.current) {
      cardRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5 + index) * 0.1;
      cardRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 0.8 + index) * 0.1;
    }
  });

  const getFileTypeColor = (type) => {
    if (type?.includes('image')) return "#4299e1";
    if (type?.includes('pdf')) return "#e53e3e";
    return "#718096";
  };

  return (
    <group ref={cardRef} position={position}>
      <RoundedBox args={[0.8, 1, 0.1]} radius={0.1} smoothness={4}>
        <meshStandardMaterial 
          color={getFileTypeColor(file.type)} 
          transparent 
          opacity={0.8}
          emissive={getFileTypeColor(file.type)}
          emissiveIntensity={0.1}
        />
      </RoundedBox>
      
      {/* File Type Icon */}
      <Box args={[0.3, 0.3, 0.05]} position={[0, 0.2, 0.1]}>
        <meshStandardMaterial 
          color="#ffffff" 
          emissive="#f7fafc"
          emissiveIntensity={0.2}
        />
      </Box>
      
      {/* File Name */}
      <Text
        position={[0, -0.3, 0.1]}
        fontSize={0.15}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        font="/fonts/Inter-Bold.woff"
        maxWidth={0.7}
      >
        {file.name?.substring(0, 10) + (file.name?.length > 10 ? '...' : '')}
      </Text>
    </group>
  );
};

// Floating Medical Document Icons
const MedicalDocumentIcons = () => {
  const iconsRef = useRef([]);
  
  useFrame((state) => {
    iconsRef.current.forEach((icon, index) => {
      if (icon) {
        icon.rotation.y = state.clock.elapsedTime * (0.3 + index * 0.1);
        icon.position.y = Math.sin(state.clock.elapsedTime * 0.6 + index) * 0.3;
      }
    });
  });

  const icons = [
    { pos: [-3, 2, -1], color: "#4299e1", type: "📋" },
    { pos: [3, 2, -1], color: "#48bb78", type: "🩺" },
    { pos: [-3, -2, -1], color: "#e53e3e", type: "💊" },
    { pos: [3, -2, -1], color: "#805ad5", type: "🔬" }
  ];

  return (
    <group>
      {icons.map((icon, index) => (
        <Float key={index} speed={1 + index * 0.2} rotationIntensity={0.3} floatIntensity={0.5}>
          <mesh ref={(el) => iconsRef.current[index] = el} position={icon.pos}>
            <Sphere args={[0.3]}>
              <meshStandardMaterial 
                color={icon.color} 
                transparent 
                opacity={0.7}
                emissive={icon.color}
                emissiveIntensity={0.2}
              />
            </Sphere>
            <Text
              position={[0, 0, 0.35]}
              fontSize={0.4}
              color="#ffffff"
              anchorX="center"
              anchorY="middle"
            >
              {icon.type}
            </Text>
          </mesh>
        </Float>
      ))}
    </group>
  );
};

// File Upload Scene
const FileUploadScene = ({ isDragOver, hasFiles, fileCount, files }) => {
  return (
    <>
      <Environment preset="studio" />
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={1} />
      <pointLight position={[-5, 5, 5]} intensity={0.5} color="#4299e1" />
      
      <FileUploadZone 
        isDragOver={isDragOver} 
        hasFiles={hasFiles} 
        fileCount={fileCount} 
      />
      
      {/* File Preview Cards */}
      {files && files.slice(0, 4).map((file, index) => (
        <FilePreviewCard 
          key={index}
          file={file}
          index={index}
          position={[
            (index % 2 === 0 ? -1 : 1) * 2.5,
            (index < 2 ? 1 : -1) * 1.5,
            0.5
          ]}
        />
      ))}
      
      <MedicalDocumentIcons />
    </>
  );
};

// Main File Upload Canvas
const FileUpload3DCanvas = ({ isDragOver, hasFiles, fileCount = 0, files = [], isVisible }) => {
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
        <FileUploadScene 
          isDragOver={isDragOver} 
          hasFiles={hasFiles} 
          fileCount={fileCount}
          files={files}
        />
        <OrbitControls 
          enableZoom={false} 
          enablePan={false} 
          autoRotate={hasFiles} 
          autoRotateSpeed={0.3}
          enableDamping
          dampingFactor={0.05}
        />
      </Canvas>
    </div>
  );
};

export default FileUpload3DCanvas;
