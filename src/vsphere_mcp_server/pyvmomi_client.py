"""pyVmomi-based vSphere client for advanced operations (clone, network binding, etc.)."""

import os
import ssl
from typing import Optional, List, Dict, Any

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl


class PyVmomiClient:
    """Context-managed pyVmomi connection to vCenter."""

    def __init__(
        self,
        host: str = None,
        user: str = None,
        password: str = None,
        port: int = 443,
    ):
        self.host = host or os.environ.get("VCENTER_HOST")
        self.user = user or os.environ.get("VCENTER_USER")
        self.password = password or os.environ.get("VCENTER_PASSWORD")
        self.port = int(os.environ.get("VCENTER_PORT", port))
        self._si = None

    @property
    def si(self):
        if self._si is None:
            self.connect()
        return self._si

    def connect(self):
        """Establish connection with SSL verification disabled."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        self._si = SmartConnect(
            host=self.host,
            user=self.user,
            pwd=self.password,
            port=self.port,
            sslContext=ctx,
        )
        return self._si

    def disconnect(self):
        if self._si:
            Disconnect(self._si)
            self._si = None

    def close(self):
        self.disconnect()

    # ── Container helpers ────────────────────────────────────────

    @property
    def content(self) -> vim.ServiceInstanceContent:
        return self.si.RetrieveContent()

    def get_container_view(self, obj_type, container=None, recursive=True) -> vim.view.ContainerView:
        """Create a ContainerView filtered by obj_type."""
        if container is None:
            container = self.content.rootFolder
        return self.content.viewManager.CreateContainerView(
            container=container,
            type=[obj_type],
            recursive=recursive,
        )

    # ── Entity lookups ───────────────────────────────────────────

    def find_datacenter(self, name: str) -> Optional[vim.Datacenter]:
        """Find a datacenter by name."""
        for dc in self.content.rootFolder.childEntity:
            if isinstance(dc, vim.Datacenter) and dc.name == name:
                return dc
        return None

    def find_vm(self, name: str, datacenter: vim.Datacenter = None) -> Optional[vim.VirtualMachine]:
        """Find a VM/template by name, optionally scoped to a datacenter."""
        root = datacenter.hostFolder if datacenter else self.content.rootFolder
        # PropertyCollector approach – reliable with all pyVmomi versions
        view_ref = self.get_container_view(vim.VirtualMachine, container=root)
        try:
            # Retrieve name property
            collector = self.content.propertyCollector
            traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(
                name="traverse",
                type=vim.view.ContainerView,
                path="view",
                skip=False,
            )
            obj_spec = vmodl.query.PropertyCollector.ObjectSpec(
                obj=view_ref,
                skip=True,
                selectSet=[traversal_spec],
            )
            prop_spec = vmodl.query.PropertyCollector.PropertySpec(
                type=vim.VirtualMachine,
                pathSet=["name", "config.template"],
                all=False,
            )
            filter_spec = vmodl.query.PropertyCollector.FilterSpec(
                objectSet=[obj_spec],
                propSet=[prop_spec],
            )
            result = collector.RetrieveProperties([filter_spec])
            for obj_content in result:
                props = {p.name: p.val for p in obj_content.propSet}
                if props.get("name") == name:
                    return obj_content.obj
        finally:
            view_ref.Destroy()
        return None

    def find_cluster(self, name: str, datacenter: vim.Datacenter = None) -> Optional[vim.ClusterComputeResource]:
        """Find a cluster by name."""
        root = datacenter.hostFolder if datacenter else self.content.rootFolder
        view_ref = self.get_container_view(vim.ClusterComputeResource, container=root)
        try:
            collector = self.content.propertyCollector
            traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(
                name="traverse",
                type=vim.view.ContainerView,
                path="view",
                skip=False,
            )
            obj_spec = vmodl.query.PropertyCollector.ObjectSpec(
                obj=view_ref,
                skip=True,
                selectSet=[traversal_spec],
            )
            prop_spec = vmodl.query.PropertyCollector.PropertySpec(
                type=vim.ClusterComputeResource,
                pathSet=["name"],
                all=False,
            )
            filter_spec = vmodl.query.PropertyCollector.FilterSpec(
                objectSet=[obj_spec],
                propSet=[prop_spec],
            )
            result = collector.RetrieveProperties([filter_spec])
            for obj_content in result:
                props = {p.name: p.val for p in obj_content.propSet}
                if props.get("name") == name:
                    return obj_content.obj
        finally:
            view_ref.Destroy()
        return None

    def find_datastore(self, name: str, datacenter: vim.Datacenter = None) -> Optional[vim.Datastore]:
        """Find a datastore by name."""
        root = datacenter.datastoreFolder if datacenter else self.content.rootFolder
        view_ref = self.get_container_view(vim.Datastore, container=root)
        try:
            collector = self.content.propertyCollector
            traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(
                name="traverse",
                type=vim.view.ContainerView,
                path="view",
                skip=False,
            )
            obj_spec = vmodl.query.PropertyCollector.ObjectSpec(
                obj=view_ref,
                skip=True,
                selectSet=[traversal_spec],
            )
            prop_spec = vmodl.query.PropertyCollector.PropertySpec(
                type=vim.Datastore,
                pathSet=["name"],
                all=False,
            )
            filter_spec = vmodl.query.PropertyCollector.FilterSpec(
                objectSet=[obj_spec],
                propSet=[prop_spec],
            )
            result = collector.RetrieveProperties([filter_spec])
            for obj_content in result:
                props = {p.name: p.val for p in obj_content.propSet}
                if props.get("name") == name:
                    return obj_content.obj
        finally:
            view_ref.Destroy()
        return None

    def find_network(self, name: str, datacenter: vim.Datacenter = None) -> Optional[vim.Network]:
        """Find a network by name."""
        root = datacenter.networkFolder if datacenter else self.content.rootFolder
        view_ref = self.get_container_view(vim.Network, container=root)
        try:
            collector = self.content.propertyCollector
            traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(
                name="traverse",
                type=vim.view.ContainerView,
                path="view",
                skip=False,
            )
            obj_spec = vmodl.query.PropertyCollector.ObjectSpec(
                obj=view_ref,
                skip=True,
                selectSet=[traversal_spec],
            )
            prop_spec = vmodl.query.PropertyCollector.PropertySpec(
                type=vim.Network,
                pathSet=["name"],
                all=False,
            )
            filter_spec = vmodl.query.PropertyCollector.FilterSpec(
                objectSet=[obj_spec],
                propSet=[prop_spec],
            )
            result = collector.RetrieveProperties([filter_spec])
            for obj_content in result:
                props = {p.name: p.val for p in obj_content.propSet}
                if props.get("name") == name:
                    return obj_content.obj
        finally:
            view_ref.Destroy()
        return None

    def get_vm_parent_folder(self, vm: vim.VirtualMachine) -> Optional[vim.Folder]:
        """Get the parent folder of a VM (used as clone target folder)."""
        # Walk parent chain to find the VM folder
        current = vm.parent
        while current is not None:
            if isinstance(current, vim.Folder):
                return current
            current = current.parent
        return None

    def get_target_folder_from_existing_vm(
        self, vm_name: str, datacenter: vim.Datacenter
    ) -> Optional[vim.Folder]:
        """Reverse-engineer clone target folder from an existing VM in the target DC."""
        vm = self.find_vm(vm_name, datacenter)
        if vm is None:
            return None
        return self.get_vm_parent_folder(vm)

    def get_any_vm_folder(self, datacenter: vim.Datacenter) -> Optional[vim.Folder]:
        """Find any VM folder in a datacenter, falling back to vmFolder root."""
        vm_folder = datacenter.vmFolder
        # Try to find a subfolder with VMs
        folders = [vm_folder]
        for entity in vm_folder.childEntity:
            if isinstance(entity, vim.Folder):
                folders.append(entity)
            elif isinstance(entity, vim.VirtualMachine):
                # There's a VM directly in vmFolder; use it directly
                return vm_folder
        return vm_folder  # Default fallback
