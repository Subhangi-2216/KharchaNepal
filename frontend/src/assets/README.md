# Assets Directory

This directory contains static assets used in the frontend application, such as:

- Images
- Icons
- Fonts
- Other static files

## Usage

Import assets in your components like this:

```tsx
import myImage from '../assets/images/my-image.png';

function MyComponent() {
  return (
    <div>
      <img src={myImage} alt="My Image" />
    </div>
  );
}
```

## Organization

Consider organizing assets into subdirectories by type:

- `/images` - For all image files (png, jpg, etc.)
- `/icons` - For icon files (svg, etc.)
- `/fonts` - For custom fonts