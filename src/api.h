/*

  This file is a part of the Python binding of the
  Nova Physics Engine project and distributed under the MIT license.

  Copyright © Kadir Aksoy
  https://github.com/kadir014/nova-physics-python

*/

#ifndef NV_PYTHON_API_H
#define NV_PYTHON_API_H

#include <Python.h>
#include "structmember.h"
#include "novaphysics/novaphysics.h"


/**********************************
            nova.Vector2
***********************************/

/**
 * Vector2 object interface
 */
typedef struct {
    PyObject_HEAD
    double x;
    double y;
} nv_Vector2Object;

/**
 * Create new Vector2 object
 */
nv_Vector2Object *nv_Vector2Object_new(double x, double y);

/**
 * Vector2 Python object to Vector2 struct
 */
#define PY_TO_VEC2(o) (NV_VEC2((o)->x, (o)->y))

/**
 * Vector2 objec type internals
 */
static PyTypeObject nv_Vector2ObjectType;

/**
 * Vector2 object deallocater
 */
static void nv_Vector2Object_dealloc(nv_Vector2Object *self);

/**
 * Vector2 object initializer
 */
static int nv_Vector2Object_init(
    nv_Vector2Object *self,
    PyObject *args,
    PyObject *kwds
);

static PyObject *nv_Vector2Object___add__(
    nv_Vector2Object *self,
    nv_Vector2Object *vector
);

static PyObject *nv_Vector2Object___sub__(
    nv_Vector2Object *self,
    nv_Vector2Object *vector
);

static PyObject *nv_Vector2Object___mul__(
    nv_Vector2Object *self,
    PyObject *scalar
);

static PyObject *nv_Vector2Object___truediv__(
    nv_Vector2Object *self,
    PyObject *scalar
);


/**********************************
             nova.Body
***********************************/

/**
 * Body object interface
 */
typedef struct {
    PyObject_HEAD
    nv_Body *body;
    nv_BodyType type;
    int shape;
    nv_Vector2Object *position;
    double angle;
    double radius;
} nv_BodyObject;

/**
 * Body object type internals
 */
static PyTypeObject nv_BodyObjectType;

/**
 * Body object deallocater
 */
static void nv_BodyObject_dealloc(nv_BodyObject *self);

/**
 * Body object initializer
 */
static int nv_BodyObject_init(
    nv_BodyObject *self,
    PyObject *args,
    PyObject *kwds
);

/**
 * Body.get_vertices() method
 * Returns transformed vertices of the body
*/
static PyObject *nv_BodyObject_get_vertices(
    nv_BodyObject *self,
    PyObject *Py_UNUSED(ignored)
);

/**
 * Body.apply_force() method
 * Applies force to center of body
*/
static PyObject *nv_BodyObject_apply_force(
    nv_BodyObject *self,
    PyObject *args
);

PyObject *nv_create_circle(PyObject *self, PyObject *args);

PyObject *nv_create_rect(PyObject *self, PyObject *args);


/**********************************
             nova.Space
***********************************/

/**
 * Space object interface
 */
typedef struct {
    PyObject_HEAD
    nv_Space *space;
    nv_Array *body_objects;
} nv_SpaceObject;

/**
 * Space object type internals
 */
static PyTypeObject nv_SpaceType;

/**
 * Space object deallocater
 */
static void nv_SpaceObject_dealloc(nv_SpaceObject *self);

/**
 * Space object initializer
 */
static int nv_SpaceObject_init(
    nv_SpaceObject *self,
    PyObject *args,
    PyObject *kwds
);

/**
 * Space.step() method
 */
static PyObject *nv_SpaceObject_step(
    nv_SpaceObject *self,
    PyObject *args
);

/**
 * Space.get_bodies() method
 * Returns nv_Space instance's bodies array as a Python tuple
 */
static PyObject *nv_SpaceObject_get_bodies(
    nv_SpaceObject *self,
    PyObject *Py_UNUSED(ignored)
);

/**
 * Space.add(body: Body) method
*/
static PyObject *nv_SpaceObject_add(
    nv_SpaceObject *self,
    PyObject *args
);


#endif